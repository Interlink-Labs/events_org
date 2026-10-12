from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.estimate import PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str | None = None
    paid_at: datetime | None = None
    comment: str | None = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_id: int
    estimate_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    method: str | None
    paid_at: datetime | None
    created_by: int | None
    confirmed_by: int | None
    confirmed_at: datetime | None
    comment: str | None
    created_at: datetime