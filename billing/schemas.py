from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

class EstimateStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    CLOSED = "closed"

class ItemType(str, Enum):
    SERVICE = "service"
    DISCOUNT = "discount"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class ItemCreate(BaseModel):
    name: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    item_type: ItemType = ItemType.SERVICE

# НОВОЕ: модель для обновления позиции (п.19 ТЗ)
class ItemUpdate(BaseModel):
    name: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)

class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str | None = None

class ExpenseCreate(BaseModel):
    name: str
    amount: Decimal = Field(ge=0)