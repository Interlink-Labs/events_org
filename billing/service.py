"""Бизнес-логика модуля «Смета и оплата»."""
from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException, status

from billing import storage
from billing.schemas import (
    EstimateStatus, ItemType, PaymentStatus,
    ItemCreate, ItemUpdate, ExpenseCreate, PaymentCreate,
)


CENTS = Decimal("0.01")


# ---------- Смета ----------

def get_or_create_estimate(event_id: int) -> dict:
    if event_id in storage.event_to_estimate:
        return storage.estimates_db[storage.event_to_estimate[event_id]]

    estimate_id = storage.next_id("estimate")
    estimate = {
        "id": estimate_id,
        "event_id": event_id,
        "status": EstimateStatus.DRAFT,
        "currency": "RUB",
        "services_total": Decimal("0.00"),
        "expenses_total": Decimal("0.00"),
        "discount_total": Decimal("0.00"),
        "total_amount": Decimal("0.00"),
        "paid_amount": Decimal("0.00"),
        "debt_amount": Decimal("0.00"),
        "overpayment_amount": Decimal("0.00"),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    storage.estimates_db[estimate_id] = estimate
    storage.event_to_estimate[event_id] = estimate_id
    return estimate


def _ensure_editable(estimate: dict) -> None:
    if estimate["status"] in (EstimateStatus.CLOSED, EstimateStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Смета в статусе '{estimate['status'].value}' не может быть изменена",
        )


def recalculate(estimate: dict) -> dict:
    items = [i for i in storage.items_db.values() if i["estimate_id"] == estimate["id"]]
    expenses = [e for e in storage.expenses_db.values() if e["estimate_id"] == estimate["id"]]
    payments = [p for p in storage.payments_db.values() if p["estimate_id"] == estimate["id"]]

    services_total = sum(
        (i["amount"] for i in items if i["item_type"] == ItemType.SERVICE), Decimal("0.00")
    )
    discount_total = sum(
        (i["amount"] for i in items if i["item_type"] == ItemType.DISCOUNT), Decimal("0.00")
    )
    expenses_total = sum((e["amount"] for e in expenses), Decimal("0.00"))
    paid_amount = sum(
        (p["amount"] for p in payments if p["status"] == PaymentStatus.CONFIRMED), Decimal("0.00")
    )

    total = (services_total + expenses_total - discount_total).quantize(CENTS)
    debt = (total - paid_amount).quantize(CENTS)
    overpay = (-debt).quantize(CENTS) if debt < 0 else Decimal("0.00")

    estimate.update({
        "services_total": services_total.quantize(CENTS),
        "discount_total": discount_total.quantize(CENTS),
        "expenses_total": expenses_total.quantize(CENTS),
        "total_amount": total,
        "paid_amount": paid_amount.quantize(CENTS),
        "debt_amount": debt if debt > 0 else Decimal("0.00"),
        "overpayment_amount": overpay,
        "updated_at": datetime.now(timezone.utc),
    })
    return estimate


def get_estimate_detail(event_id: int) -> dict:
    estimate = get_or_create_estimate(event_id)
    items = [i for i in storage.items_db.values() if i["estimate_id"] == estimate["id"]]
    expenses = [e for e in storage.expenses_db.values() if e["estimate_id"] == estimate["id"]]
    return {**estimate, "items": items, "expenses": expenses}


def set_status(event_id: int, new_status: EstimateStatus) -> dict:
    estimate = get_or_create_estimate(event_id)
    if estimate["status"] in (EstimateStatus.CLOSED, EstimateStatus.CANCELLED):
        raise HTTPException(status_code=409, detail="Смета уже закрыта/отменена")
    estimate["status"] = new_status
    estimate["updated_at"] = datetime.now(timezone.utc)
    return estimate


# ---------- Позиции сметы ----------

def add_item(event_id: int, payload: ItemCreate) -> dict:
    estimate = get_or_create_estimate(event_id)
    _ensure_editable(estimate)

    amount = (payload.quantity * payload.unit_price).quantize(CENTS)
    item_id = storage.next_id("item")
    item = {
        "id": item_id,
        "estimate_id": estimate["id"],
        "name": payload.name,
        "unit": payload.unit,
        "quantity": payload.quantity,
        "unit_price": payload.unit_price,
        "amount": amount,
        "item_type": payload.item_type,
        "contractor_id": payload.contractor_id,
        "responsible_user_id": payload.responsible_user_id,
        "comment": payload.comment,
    }
    storage.items_db[item_id] = item
    recalculate(estimate)
    return item


def update_item(event_id: int, item_id: int, payload: ItemUpdate) -> dict:
    estimate = get_or_create_estimate(event_id)
    _ensure_editable(estimate)

    item = storage.items_db.get(item_id)
    if not item or item["estimate_id"] != estimate["id"]:
        raise HTTPException(status_code=404, detail="Позиция сметы не найдена")

    if payload.quantity is not None:
        item["quantity"] = payload.quantity
    if payload.unit_price is not None:
        item["unit_price"] = payload.unit_price
    if payload.comment is not None:
        item["comment"] = payload.comment

    item["amount"] = (item["quantity"] * item["unit_price"]).quantize(CENTS)
    recalculate(estimate)
    return item


def delete_item(event_id: int, item_id: int) -> None:
    estimate = get_or_create_estimate(event_id)
    _ensure_editable(estimate)

    item = storage.items_db.get(item_id)
    if not item or item["estimate_id"] != estimate["id"]:
        raise HTTPException(status_code=404, detail="Позиция сметы не найдена")

    del storage.items_db[item_id]
    recalculate(estimate)


# ---------- Доп. расходы ----------

def add_expense(event_id: int, payload: ExpenseCreate) -> dict:
    estimate = get_or_create_estimate(event_id)
    _ensure_editable(estimate)

    expense_id = storage.next_id("expense")
    expense = {
        "id": expense_id,
        "estimate_id": estimate["id"],
        "name": payload.name,
        "amount": payload.amount.quantize(CENTS),
        "comment": payload.comment,
    }
    storage.expenses_db[expense_id] = expense
    recalculate(estimate)
    return expense


def delete_expense(event_id: int, expense_id: int) -> None:
    estimate = get_or_create_estimate(event_id)
    _ensure_editable(estimate)

    expense = storage.expenses_db.get(expense_id)
    if not expense or expense["estimate_id"] != estimate["id"]:
        raise HTTPException(status_code=404, detail="Расход не найден")

    del storage.expenses_db[expense_id]
    recalculate(estimate)


# ---------- Платежи ----------

def create_payment(event_id: int, payload: PaymentCreate) -> dict:
    estimate = get_or_create_estimate(event_id)

    payment_id = storage.next_id("payment")
    payment = {
        "id": payment_id,
        "event_id": event_id,
        "estimate_id": estimate["id"],
        "amount": payload.amount.quantize(CENTS),
        "currency": estimate["currency"],
        "status": PaymentStatus.PENDING,
        "method": payload.method,
        "comment": payload.comment,
        "created_at": datetime.now(timezone.utc),
    }
    storage.payments_db[payment_id] = payment
    storage.payment_logs_db[payment_id] = [{
        "old_status": None,
        "new_status": PaymentStatus.PENDING,
        "changed_at": datetime.now(timezone.utc),
    }]
    return payment


def _change_payment_status(payment: dict, new_status: PaymentStatus, comment: str | None = None) -> dict:
    log = {
        "old_status": payment["status"],
        "new_status": new_status,
        "changed_at": datetime.now(timezone.utc),
        "comment": comment,
    }
    storage.payment_logs_db.setdefault(payment["id"], []).append(log)
    payment["status"] = new_status

    estimate = storage.estimates_db[payment["estimate_id"]]
    recalculate(estimate)
    return payment


def confirm_payment(payment_id: int) -> dict:
    payment = storage.payments_db.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    if payment["status"] != PaymentStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Нельзя подтвердить платёж в статусе {payment['status'].value}")
    return _change_payment_status(payment, PaymentStatus.CONFIRMED)


def cancel_payment(payment_id: int) -> dict:
    payment = storage.payments_db.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    if payment["status"] in (PaymentStatus.CANCELLED, PaymentStatus.REFUNDED):
        raise HTTPException(status_code=409, detail="Платёж уже отменён/возвращён")
    return _change_payment_status(payment, PaymentStatus.CANCELLED)


def refund_payment(payment_id: int) -> dict:
    payment = storage.payments_db.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    if payment["status"] != PaymentStatus.CONFIRMED:
        raise HTTPException(status_code=409, detail="Возврат возможен только по подтверждённому платежу")
    return _change_payment_status(payment, PaymentStatus.REFUNDED)


def list_payments(event_id: int) -> list[dict]:
    return [p for p in storage.payments_db.values() if p["event_id"] == event_id]