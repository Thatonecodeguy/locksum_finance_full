from __future__ import annotations
from fastapi import HTTPException, status
from . import models

PLAN_ORDER = {
    "free": 0,
    "plus": 1,
    "pro": 2,
}

def require_min_plan(user: models.User, min_plan: str = "plus"):
    current = PLAN_ORDER.get(user.plan, 0)
    required = PLAN_ORDER.get(min_plan, 1)
    if current < required or user.subscription_status not in {"active", "trialing"}:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"{min_plan.capitalize()} plan (or higher) required for this feature.",
        )
