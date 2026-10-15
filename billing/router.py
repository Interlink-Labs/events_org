from fastapi import APIRouter, status
from billing import service
from billing.schemas import (
    EstimateDetail, EstimateRead, EstimateStatusUpdate,
    ItemCreate, ItemRead, ItemUpdate,
    ExpenseCreate, ExpenseRead,
    PaymentCreate, PaymentRead,
)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


# ---------- Смета ----------

@router.get("/events/{event_id}/estimate", response_model=EstimateDetail)
def get_estimate(event_id: int):
    return service.get_estimate_detail(event_id)


@router.patch("/events/{event_id}/estimate/status", response_model=EstimateRead)
def update_estimate_status(event_id: int, payload: EstimateStatusUpdate):
    return service.set_status(event_id, payload.status)


@router.post("/events/{event_id}/estimate/recalculate", response_model=EstimateRead)
def recalculate_estimate(event_id: int):
    return service.recalculate(service.get_or_create_estimate(event_id))


# ---------- Позиции сметы ----------

@router.post("/events/{event_id}/estimate/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def add_item(event_id: int, payload: ItemCreate):
    return service.add_item(event_id, payload)


@router.patch("/events/{event_id}/estimate/items/{item_id}", response_model=ItemRead)
def update_item(event_id: int, item_id: int, payload: ItemUpdate):
    return service.update_item(event_id, item_id, payload)


@router.delete("/events/{event_id}/estimate/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(event_id: int, item_id: int):
    service.delete_item(event_id, item_id)


# ---------- Доп. расходы ----------

@router.post("/events/{event_id}/estimate/expenses", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def add_expense(event_id: int, payload: ExpenseCreate):
    return service.add_expense(event_id, payload)


@router.delete("/events/{event_id}/estimate/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(event_id: int, expense_id: int):
    service.delete_expense(event_id, expense_id)


# ---------- Платежи ----------

@router.get("/events/{event_id}/payments", response_model=list[PaymentRead])
def list_payments(event_id: int):
    return service.list_payments(event_id)


@router.post("/events/{event_id}/payments", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(event_id: int, payload: PaymentCreate):
    return service.create_payment(event_id, payload)


@router.patch("/payments/{payment_id}/confirm", response_model=PaymentRead)
def confirm_payment(payment_id: int):
    return service.confirm_payment(payment_id)


@router.patch("/payments/{payment_id}/cancel", response_model=PaymentRead)
def cancel_payment(payment_id: int):
    return service.cancel_payment(payment_id)


@router.patch("/payments/{payment_id}/refund", response_model=PaymentRead)
def refund_payment(payment_id: int):
    return service.refund_payment(payment_id)