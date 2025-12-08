from __future__ import annotations
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Core
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")

    # Auth / JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "CHANGE_ME_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Plaid
    PLAID_CLIENT_ID: str | None = os.getenv("PLAID_CLIENT_ID")
    PLAID_SECRET: str | None = os.getenv("PLAID_SECRET")
    PLAID_ENV: str = os.getenv("PLAID_ENV", "sandbox")
    PLAID_REDIRECT_URI: str | None = os.getenv("PLAID_REDIRECT_URI")

    # Stripe
    STRIPE_SECRET: str | None = os.getenv("STRIPE_SECRET")
    STRIPE_WEBHOOK_SECRET: str | None = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID_PLUS_MONTHLY: str | None = os.getenv("STRIPE_PRICE_ID_PLUS_MONTHLY")
    STRIPE_PRICE_ID_PLUS_YEARLY: str | None = os.getenv("STRIPE_PRICE_ID_PLUS_YEARLY")
    STRIPE_PRICE_ID_PRO_MONTHLY: str | None = os.getenv("STRIPE_PRICE_ID_PRO_MONTHLY")
    STRIPE_PRICE_ID_PRO_YEARLY: str | None = os.getenv("STRIPE_PRICE_ID_PRO_YEARLY")

settings = Settings()
