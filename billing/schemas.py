from decimal import Decimal
from pydantic import BaseModel, Field

from models import EstimateStatus, PaymentStatus, ItemType

class ItemCreate(BaseModel):
    name: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    item_type: ItemType = ItemType.SERVICE

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

class EstimateStatusUpdate(BaseModel):
    status: EstimateStatus