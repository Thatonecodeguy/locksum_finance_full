from __future__ import annotations
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from plaid import Client
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

from .database import get_db
from .settings import settings
from . import models, schemas
from .auth import get_current_user

router = APIRouter(prefix="/plaid", tags=["Plaid"])

def _plaid_client() -> plaid_api.PlaidApi:
    if not settings.PLAID_CLIENT_ID or not settings.PLAID_SECRET:
        raise RuntimeError("Plaid keys not configured")
    configuration = Client(
        client_id=settings.PLAID_CLIENT_ID,
        secret=settings.PLAID_SECRET,
        environment=settings.PLAID_ENV,
    ).configuration
    api_client = plaid_api.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)

@router.post("/link-token", response_model=schemas.PlaidLinkTokenOut)
def create_link_token(user=Depends(get_current_user)):
    client = _plaid_client()
    req = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="Locksum Finance",
        country_codes=[CountryCode("US")],
        language="en",
        user=LinkTokenCreateRequestUser(client_user_id=str(user.id)),
        redirect_uri=settings.PLAID_REDIRECT_URI,
    )
    resp = client.link_token_create(req)
    return schemas.PlaidLinkTokenOut(link_token=resp["link_token"])

@router.post("/exchange", response_model=dict)
def exchange_public_token(
    body: schemas.PlaidPublicTokenExchange,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    client = _plaid_client()
    req = ItemPublicTokenExchangeRequest(public_token=body.public_token)
    resp = client.item_public_token_exchange(req)
    access_token = resp["access_token"]
    item_id = resp["item_id"]

    existing = (
        db.query(models.PlaidItem)
        .filter(models.PlaidItem.user_id == user.id, models.PlaidItem.item_id == item_id)
        .first()
    )
    if not existing:
        item = models.PlaidItem(
            user_id=user.id,
            access_token=access_token,
            item_id=item_id,
            institution_name=body.institution_name or "",
        )
        db.add(item)
    else:
        existing.access_token = access_token
    db.commit()
    return {"status": "linked", "item_id": item_id}
