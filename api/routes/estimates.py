from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.estimate import EstimateStatus, ItemType


class EstimateItemCreate(BaseModel):
    service_id: int | None = None
    contractor_id: int | None = None
    responsible_user_id: int | None = None
    name_snapshot: str | None = None
    unit: str = "шт"
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    item_type: ItemType = ItemType.SERVICE
    comment: str | None = None


class EstimateItemUpdate(BaseModel):
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    comment: str | None = None


class EstimateItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service_id: int | None
    contractor_id: int | None
    responsible_user_id: int | None
    name_snapshot: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    item_type: ItemType
    comment: str | None


class AdditionalExpenseCreate(BaseModel):
    name: str
    amount: Decimal = Field(ge=0)
    comment: str | None = None


class AdditionalExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    amount: Decimal
    comment: str | None


class EstimateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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
    created_at: datetime
    updated_at: datetime
    items: list[EstimateItemRead] = []
    expenses: list[AdditionalExpenseRead] = []