from __future__ import annotations
import json
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .settings import settings
from .database import get_db
from . import models, schemas
from .auth import get_current_user

router = APIRouter(prefix="/billing", tags=["Billing"])

def _setup_stripe():
    if not settings.STRIPE_SECRET:
        raise RuntimeError("STRIPE_SECRET not configured")
    stripe.api_key = settings.STRIPE_SECRET

def _price_for(plan: str, interval: str) -> str:
    plan = plan.lower()
    interval = interval.lower()
    if plan == "plus" and interval == "monthly":
        return settings.STRIPE_PRICE_ID_PLUS_MONTHLY
    if plan == "plus" and interval == "yearly":
        return settings.STRIPE_PRICE_ID_PLUS_YEARLY
    if plan == "pro" and interval == "monthly":
        return settings.STRIPE_PRICE_ID_PRO_MONTHLY
    if plan == "pro" and interval == "yearly":
        return settings.STRIPE_PRICE_ID_PRO_YEARLY
    return None

@router.post("/checkout-session", response_model=schemas.StripeCheckoutSessionOut)
def create_checkout_session(
    body: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _setup_stripe()
    price_id = _price_for(body.plan, body.interval)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan or interval")

    if not user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": user.id},
        )
        user.stripe_customer_id = customer["id"]
        db.add(user)
        db.commit()

    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        success_url=f"{settings.FRONTEND_BASE_URL}/billing/success",
        cancel_url=f"{settings.FRONTEND_BASE_URL}/billing/cancel",
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
    )
    return schemas.StripeCheckoutSessionOut(url=session.url)

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    _setup_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        event = stripe.Event.construct_from(
            json.loads(payload.decode()), stripe.api_key
        )

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type.startswith("customer.subscription."):
        customer_id = obj["customer"]
        status = obj["status"]  # active, trialing, past_due, canceled, etc.
        plan_price_id = obj["items"]["data"][0]["price"]["id"]
        interval = obj["items"]["data"][0]["price"]["recurring"]["interval"]  # month or year

        user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
        if user:
            # map back to plan name
            plan = "free"
            if plan_price_id in {
                settings.STRIPE_PRICE_ID_PLUS_MONTHLY,
                settings.STRIPE_PRICE_ID_PLUS_YEARLY,
            }:
                plan = "plus"
            elif plan_price_id in {
                settings.STRIPE_PRICE_ID_PRO_MONTHLY,
                settings.STRIPE_PRICE_ID_PRO_YEARLY,
            }:
                plan = "pro"

            user.subscription_status = status
            user.plan = plan
            user.plan_interval = "monthly" if interval == "month" else "yearly"
            db.add(user)
            db.commit()

    return {"received": True}
