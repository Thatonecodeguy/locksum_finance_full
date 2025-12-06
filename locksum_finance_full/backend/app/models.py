from __future__ import annotations
import datetime as dt
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[str] = mapped_column(String(32), default="free")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user")
    budgets: Mapped[List["Budget"]] = relationship(back_populates="user")

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
