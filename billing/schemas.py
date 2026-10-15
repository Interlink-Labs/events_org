from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


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


# ---------- Позиции сметы ----------

class ItemCreate(BaseModel):
    name: str
    unit: str = "шт"
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    item_type: ItemType = ItemType.SERVICE
    contractor_id: int | None = None
    responsible_user_id: int | None = None
    comment: str | None = None


class ItemUpdate(BaseModel):
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    comment: str | None = None


class ItemRead(BaseModel):
    id: int
    estimate_id: int
    name: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    item_type: ItemType
    contractor_id: int | None
    responsible_user_id: int | None
    comment: str | None


# ---------- Доп. расходы ----------

class ExpenseCreate(BaseModel):
    name: str
    amount: Decimal = Field(ge=0)
    comment: str | None = None


class ExpenseRead(BaseModel):
    id: int
    estimate_id: int
    name: str
    amount: Decimal
    comment: str | None


# ---------- Смета ----------

class EstimateRead(BaseModel):
    id: int
    event_id: int
    status: EstimateStatus
    currency: str
    services_total: Decimal
    expenses_total: Decimal
    discount_total: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    debt_amount: Decimal
    overpayment_amount: Decimal


class EstimateDetail(EstimateRead):
    items: list[ItemRead] = []
    expenses: list[ExpenseRead] = []


class EstimateStatusUpdate(BaseModel):
    status: EstimateStatus


# ---------- Платежи ----------

class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str | None = None
    comment: str | None = None


class PaymentRead(BaseModel):
    id: int
    event_id: int
    estimate_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    method: str | None
    comment: str | None