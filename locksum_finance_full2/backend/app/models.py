from __future__ import annotations
import datetime as dt
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    # Subscription & plan
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[str] = mapped_column(String(32), default="free")  # free | active | past_due | canceled
    plan: Mapped[str] = mapped_column(String(16), default="free")  # free | plus | pro
    plan_interval: Mapped[str] = mapped_column(String(16), default="monthly")  # monthly | yearly

    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    budgets: Mapped[List["Budget"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    plaid_items: Mapped[List["PlaidItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    date: Mapped[dt.date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(128), default="Uncategorized")
    user: Mapped["User"] = relationship(back_populates="transactions")

class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category: Mapped[str] = mapped_column(String(128))
    limit_amount: Mapped[float] = mapped_column(Float)
    user: Mapped["User"] = relationship(back_populates="budgets")

class PlaidItem(Base):
    __tablename__ = "plaid_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    access_token: Mapped[str] = mapped_column(String(512))
    item_id: Mapped[str] = mapped_column(String(255))
    institution_name: Mapped[str] = mapped_column(String(255), default="")
    user: Mapped["User"] = relationship(back_populates="plaid_items")
