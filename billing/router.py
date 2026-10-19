from fastapi import APIRouter, HTTPException, status
from decimal import Decimal
from billing import storage
from billing.schemas import (
    ItemCreate, ItemUpdate, PaymentCreate, ExpenseCreate, 
    EstimateStatus, PaymentStatus, ItemType
)

router = APIRouter(prefix="/api/v1/billing", tags=["Смета и оплата"])

def get_or_create_est(event_id: int):
    if event_id not in storage.event_to_estimate:
        est_id = storage.next_id("estimate")
        storage.estimates_db[est_id] = {
            "id": est_id, "event_id": event_id, "status": EstimateStatus.DRAFT,
            "services_total": Decimal("0.00"), "expenses_total": Decimal("0.00"),
            "total_amount": Decimal("0.00"), "paid_amount": Decimal("0.00"), 
            "debt_amount": Decimal("0.00")
        }
        storage.event_to_estimate[event_id] = est_id
    return storage.estimates_db[storage.event_to_estimate[event_id]]

def recalculate(est_id: int):
    """Автоматический пересчет всей сметы (п. 18 ТЗ)"""
    est = storage.estimates_db[est_id]
    items = [i for i in storage.items_db.values() if i["estimate_id"] == est_id]
    expenses = [e for e in storage.expenses_db.values() if e["estimate_id"] == est_id]
    payments = [p for p in storage.payments_db.values() if p["estimate_id"] == est_id]
    
    # Считаем услуги и расходы
    services_total = sum(i["amount"] for i in items if i["item_type"] == ItemType.SERVICE)
    discounts = sum(i["amount"] for i in items if i["item_type"] == ItemType.DISCOUNT)
    expenses_total = sum(e["amount"] for e in expenses)
    
    # Считаем только ПОДТВЕРЖДЕННЫЕ платежи
    paid = sum(p["amount"] for p in payments if p["status"] == PaymentStatus.CONFIRMED)
    
    total = services_total + expenses_total - discounts
    
    est["services_total"] = services_total
    est["expenses_total"] = expenses_total
    est["total_amount"] = total
    est["paid_amount"] = paid
    est["debt_amount"] = total - paid if total > paid else Decimal("0.00")

# ==================== СМЕТА И ПОЗИЦИИ ====================

@router.get("/events/{event_id}/estimate")
def get_estimate(event_id: int):
    """Просмотр всей сметы с деталями"""
    est = get_or_create_est(event_id)
    items = [i for i in storage.items_db.values() if i["estimate_id"] == est["id"]]
    expenses = [e for e in storage.expenses_db.values() if e["estimate_id"] == est["id"]]
    return {**est, "items": items, "expenses": expenses}

@router.post("/events/{event_id}/estimate/items")
def add_item(event_id: int, item: ItemCreate):
    """Добавление услуги в смету"""
    est = get_or_create_est(event_id)
    item_id = storage.next_id("item")
    amount = item.quantity * item.unit_price
    storage.items_db[item_id] = {
        "id": item_id, "estimate_id": est["id"], "name": item.name,
        "quantity": item.quantity, "unit_price": item.unit_price, 
        "amount": amount, "item_type": item.item_type
    }
    recalculate(est["id"])
    return {"ok": True, "item_id": item_id, "total": est["total_amount"]}

@router.patch("/events/{event_id}/estimate/items/{item_id}")
def update_item(event_id: int, item_id: int, item: ItemUpdate):
    """Изменение состава услуг (п.19 ТЗ)"""
    if item_id not in storage.items_db:
        raise HTTPException(404, "Позиция не найдена")
    
    db_item = storage.items_db[item_id]
    if item.name is not None: db_item["name"] = item.name
    if item.quantity is not None: db_item["quantity"] = item.quantity
    if item.unit_price is not None: db_item["unit_price"] = item.unit_price
    
    # Пересчитываем сумму позиции
    db_item["amount"] = db_item["quantity"] * db_item["unit_price"]
    
    est = get_or_create_est(event_id)
    recalculate(est["id"])
    return {"ok": True, "msg": "Позиция обновлена", "new_total": est["total_amount"]}

@router.delete("/events/{event_id}/estimate/items/{item_id}")
def delete_item(event_id: int, item_id: int):
    """Удаление услуги из сметы (п.19 ТЗ)"""
    if item_id not in storage.items_db:
        raise HTTPException(404, "Позиция не найдена")
    
    del storage.items_db[item_id]
    est = get_or_create_est(event_id)
    recalculate(est["id"])
    return {"ok": True, "msg": "Позиция удалена", "new_total": est["total_amount"]}

# ==================== ДОПОЛНИТЕЛЬНЫЕ РАСХОДЫ ====================

@router.post("/events/{event_id}/estimate/expenses")
def add_expense(event_id: int, exp: ExpenseCreate):
    est = get_or_create_est(event_id)
    exp_id = storage.next_id("expense")
    storage.expenses_db[exp_id] = {
        "id": exp_id, "estimate_id": est["id"], "name": exp.name, "amount": exp.amount
    }
    recalculate(est["id"])
    return {"ok": True, "expense_id": exp_id, "total": est["total_amount"]}

@router.delete("/events/{event_id}/estimate/expenses/{expense_id}")
def delete_expense(event_id: int, expense_id: int):
    """Удаление доп. расхода (п.19 ТЗ)"""
    if expense_id not in storage.expenses_db:
        raise HTTPException(404, "Расход не найден")
    
    del storage.expenses_db[expense_id]
    est = get_or_create_est(event_id)
    recalculate(est["id"])
    return {"ok": True, "msg": "Расход удален", "new_total": est["total_amount"]}

# ==================== ПЛАТЕЖИ И ИСТОРИЯ ====================

@router.get("/events/{event_id}/payments")
def get_payment_history(event_id: int):
    """Ведение истории платежей (п.21 ТЗ)"""
    est = get_or_create_est(event_id)
    return [p for p in storage.payments_db.values() if p["estimate_id"] == est["id"]]

@router.post("/events/{event_id}/payments")
def create_payment(event_id: int, pay: PaymentCreate):
    est = get_or_create_est(event_id)
    pay_id = storage.next_id("payment")
    storage.payments_db[pay_id] = {
        "id": pay_id, "estimate_id": est["id"], "amount": pay.amount, 
        "method": pay.method, "status": PaymentStatus.PENDING
    }
    return {"ok": True, "payment_id": pay_id, "status": "pending"}

@router.post("/payments/{payment_id}/confirm")
def confirm_payment(payment_id: int):
    """Подтверждение оплаты (уменьшает долг)"""
    if payment_id not in storage.payments_db:
        raise HTTPException(404, "Платёж не найден")
    
    payment = storage.payments_db[payment_id]
    payment["status"] = PaymentStatus.CONFIRMED
    recalculate(payment["estimate_id"])
    
    est = storage.estimates_db[payment["estimate_id"]]
    return {"ok": True, "msg": "Платёж подтвержден", "remaining_debt": est["debt_amount"]}

@router.post("/payments/{payment_id}/cancel")
def cancel_payment(payment_id: int):
    """Отмена платежа (если ошиблись)"""
    if payment_id not in storage.payments_db:
        raise HTTPException(404, "Платёж не найден")
    
    payment = storage.payments_db[payment_id]
    payment["status"] = PaymentStatus.CANCELLED
    recalculate(payment["estimate_id"])
    
    est = storage.estimates_db[payment["estimate_id"]]
    return {"ok": True, "msg": "Платёж отменен", "actual_debt": est["debt_amount"]}