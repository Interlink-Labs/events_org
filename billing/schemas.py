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

class ItemCreate(BaseModel):
    name: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    item_type: ItemType = ItemType.SERVICE

class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str | None = None

class ExpenseCreate(BaseModel):
    name: str
    amount: Decimal = Field(ge=0)