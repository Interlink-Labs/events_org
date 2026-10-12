from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import (
    ForeignKey, Numeric, String, Integer, DateTime, Enum as SAEnum, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class EstimateStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ItemType(str, Enum):
    SERVICE = "service"
    DISCOUNT = "discount"
    ADDITIONAL = "additional"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Estimate(Base):
    __tablename__ = "estimates"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), unique=True, index=True)
    status: Mapped[EstimateStatus] = mapped_column(SAEnum(EstimateStatus), default=EstimateStatus.DRAFT)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")

    services_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    expenses_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    debt_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    overpayment_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["EstimateItem"]] = relationship(back_populates="estimate", cascade="all, delete-orphan")
    expenses: Mapped[list["AdditionalExpense"]] = relationship(back_populates="estimate", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="estimate")


class EstimateItem(Base):
    __tablename__ = "estimate_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id"), nullable=True)
    contractor_id: Mapped[int | None] = mapped_column(ForeignKey("contractors.id"), nullable=True)
    responsible_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    name_snapshot: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(32), default="шт")
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    item_type: Mapped[ItemType] = mapped_column(SAEnum(ItemType), default=ItemType.SERVICE)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    estimate: Mapped[Estimate] = relationship(back_populates="items")


class AdditionalExpense(Base):
    __tablename__ = "additional_expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    estimate: Mapped[Estimate] = relationship(back_populates="expenses")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    confirmed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    estimate: Mapped[Estimate] = relationship(back_populates="payments")
    status_logs: Mapped[list["PaymentStatusLog"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )


class PaymentStatusLog(Base):
    __tablename__ = "payment_status_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True)
    old_status: Mapped[PaymentStatus | None] = mapped_column(SAEnum(PaymentStatus), nullable=True)
    new_status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus))
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    payment: Mapped[Payment] = relationship(back_populates="status_logs")