from fastapi import APIRouter, HTTPException
from decimal import Decimal
from datetime import datetime, timezone
from billing import storage
from billing.schemas import ItemCreate, PaymentCreate, ExpenseCreate, EstimateStatus, PaymentStatus, ItemType

router = APIRouter(prefix="/api/v1/billing", tags=["Смета и оплата"])

def get_or_create_est(event_id: int):
    if event_id not in storage.event_to_estimate:
        est_id = storage.next_id("estimate")
        storage.estimates_db[est_id] = {
            "id": est_id, "event_id": event_id, "status": EstimateStatus.DRAFT,
            "total_amount": Decimal("0.00"), "debt_amount": Decimal("0.00"), "paid_amount": Decimal("0.00")
        }
        storage.event_to_estimate[event_id] = est_id
    return storage.estimates_db[storage.event_to_estimate[event_id]]

def recalculate(est_id: int):
    est = storage.estimates_db[est_id]
    items = [i for i in storage.items_db.values() if i["estimate_id"] == est_id]
    expenses = [e for e in storage.expenses_db.values() if e["estimate_id"] == est_id]
    payments = [p for p in storage.payments_db.values() if p["estimate_id"] == est_id]
    
    total = sum(i["amount"] for i in items) + sum(e["amount"] for e in expenses)
    paid = sum(p["amount"] for p in payments if p["status"] == PaymentStatus.CONFIRMED)
    
    est["total_amount"] = total
    est["paid_amount"] = paid
    est["debt_amount"] = total - paid if total > paid else Decimal("0.00")

@router.get("/events/{event_id}/estimate")
def get_estimate(event_id: int):
    est = get_or_create_est(event_id)
    items = [i for i in storage.items_db.values() if i["estimate_id"] == est["id"]]
    return {**est, "items": items}

@router.post("/events/{event_id}/estimate/items")
def add_item(event_id: int, item: ItemCreate):
    est = get_or_create_est(event_id)
    item_id = storage.next_id("item")
    amount = item.quantity * item.unit_price
    storage.items_db[item_id] = {
        "id": item_id, "estimate_id": est["id"], "name": item.name,
        "quantity": item.quantity, "unit_price": item.unit_price, "amount": amount
    }
    recalculate(est["id"])
    return {"ok": True, "item_id": item_id, "total": est["total_amount"]}

@router.post("/events/{event_id}/estimate/expenses")
def add_expense(event_id: int, exp: ExpenseCreate):
    est = get_or_create_est(event_id)
    exp_id = storage.next_id("expense")
    storage.expenses_db[exp_id] = {"id": exp_id, "estimate_id": est["id"], "name": exp.name, "amount": exp.amount}
    recalculate(est["id"])
    return {"ok": True, "expense_id": exp_id, "total": est["total_amount"]}

@router.post("/events/{event_id}/payments")
def create_payment(event_id: int, pay: PaymentCreate):
    est = get_or_create_est(event_id)
    pay_id = storage.next_id("payment")
    storage.payments_db[pay_id] = {
        "id": pay_id, "estimate_id": est["id"], "amount": pay.amount, "status": PaymentStatus.PENDING
    }
    return {"ok": True, "payment_id": pay_id, "status": "pending"}

@router.post("/payments/{payment_id}/confirm")
def confirm_payment(payment_id: int):
    if payment_id not in storage.payments_db:
        raise HTTPException(404, "Платёж не найден")
    payment = storage.payments_db[payment_id]
    payment["status"] = PaymentStatus.CONFIRMED
    recalculate(payment["estimate_id"])
    return {"ok": True, "msg": "Платёж подтвержден", "debt": storage.estimates_db[payment["estimate_id"]]["debt_amount"]}