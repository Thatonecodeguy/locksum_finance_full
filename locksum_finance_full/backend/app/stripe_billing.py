from __future__ import annotations
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

@router.post("/checkout-session", response_model=schemas.StripeCheckoutSessionOut)
def create_checkout_session(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _setup_stripe()
    if not settings.STRIPE_PRICE_ID:
        raise HTTPException(status_code=500, detail="Stripe price not configured")

    # Ensure customer
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
        line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
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

    # Map subscription events to user
    if event_type.startswith("customer.subscription."):
        customer_id = obj["customer"]
        status = obj["status"]
        user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = status
            db.add(user)
            db.commit()

    return {"received": True}
