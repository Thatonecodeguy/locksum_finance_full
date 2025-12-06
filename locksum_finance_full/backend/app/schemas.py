from __future__ import annotations
import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TransactionBase(BaseModel):
    name: str
    amount: float
    date: dt.date
    category: str

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: int
    class Config:
        orm_mode = True

class BudgetBase(BaseModel):
    category: str
    limit_amount: float

class BudgetCreate(BudgetBase):
    pass

class BudgetOut(BudgetBase):
    id: int
    class Config:
        orm_mode = True


class AIGoals(BaseModel):
    monthly_savings_target: float | None = None

class DebtPlanRequest(BaseModel):
    total_debt: float
    monthly_extra: float
    risk: str = "medium"


class PlaidLinkTokenOut(BaseModel):
    link_token: str

class PlaidPublicTokenExchange(BaseModel):
    public_token: str
    institution_name: str | None = None

class StripeCheckoutSessionOut(BaseModel):
    url: str
