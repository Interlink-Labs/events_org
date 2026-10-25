from fastapi import APIRouter, HTTPException
from decimal import Decimal
from billing import storage
from billing.schemas import (
    ItemCreate, ItemUpdate, PaymentCreate, ExpenseCreate, EstimateStatusUpdate,
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
            "debt_amount": Decimal("0.00"), "overpayment_amount": Decimal("0.00")
        }
        storage.event_to_estimate[event_id] = est_id
    return storage.estimates_db[storage.event_to_estimate[event_id]]

def recalculate(est_id: int):
    """Глубокий пересчет сметы с учетом переплат"""
    est = storage.estimates_db[est_id]
    items = [i for i in storage.items_db.values() if i["estimate_id"] == est_id]
    expenses = [e for e in storage.expenses_db.values() if e["estimate_id"] == est_id]
    payments = [p for p in storage.payments_db.values() if p["estimate_id"] == est_id]
    
    services_total = sum(i["amount"] for i in items if i["item_type"] == ItemType.SERVICE)
    discounts = sum(i["amount"] for i in items if i["item_type"] == ItemType.DISCOUNT)
    expenses_total = sum(e["amount"] for e in expenses)
    
    # Считаем только подтвержденные деньги
    paid = sum(p["amount"] for p in payments if p["status"] == PaymentStatus.CONFIRMED)
    
    total = services_total + expenses_total - discounts
    
    est["services_total"] = services_total
    est["expenses_total"] = expenses_total
    est["total_amount"] = total
    est["paid_amount"] = paid
    
    # Разделяем долг и переплату
    if total > paid:
        est["debt_amount"] = total - paid
        est["overpayment_amount"] = Decimal("0.00")
    elif paid > total:
        est["debt_amount"] = Decimal("0.00")
        est["overpayment_amount"] = paid - total
    else:
        est["debt_amount"] = Decimal("0.00")
        est["overpayment_amount"] = Decimal("0.00")
        
    # Автоматическая смена статуса сметы, если она полностью оплачена
    if est["status"] == EstimateStatus.APPROVED and est["debt_amount"] == 0 and total > 0:
        est["status"] = EstimateStatus.PAID

def log_payment_action(payment_id: int, action: str, old_status: str, new_status: str):
    """Вспомогательная функция для логов"""
    log_id = storage.next_id("log")
    storage.payment_logs_db[log_id] = {
        "id": log_id, "payment_id": payment_id, "action": action,
        "old_status": old_status, "new_status": new_status
    }

# ==================== СМЕТА И ПОЗИЦИИ ====================

@router.get("/events/{event_id}/estimate")
def get_estimate(event_id: int):
    est = get_or_create_est(event_id)
    items = [i for i in storage.items_db.values() if i["estimate_id"] == est["id"]]
    expenses = [e for e in storage.expenses_db.values() if e["estimate_id"] == est["id"]]
    return {**est, "items": items, "expenses": expenses}

# НОВОЕ: Смена статуса сметы
@router.patch("/events/{event_id}/estimate/status")
def update_estimate_status(event_id: int, payload: EstimateStatusUpdate):
    est = get_or_create_est(event_id)
    if est["status"] in [EstimateStatus.CLOSED, EstimateStatus.CANCELLED]:
        raise HTTPException(400, "Нельзя изменить статус закрытой или отмененной сметы")
    
    est["status"] = payload.status
    return {"ok": True, "new_status": est["status"]}

@router.post("/events/{event_id}/estimate/items")
def add_item(event_id: int, item: ItemCreate):
    est = get_or_create_est(event_id)
    if est["status"] not in [EstimateStatus.DRAFT, EstimateStatus.PENDING]:
        raise HTTPException(400, "Нельзя менять состав утвержденной/оплаченной сметы")

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
    est = get_or_create_est(event_id)
    if est["status"] not in [EstimateStatus.DRAFT, EstimateStatus.PENDING]:
        raise HTTPException(400, "Смета уже утверждена, изменения запрещены")
        
    if item_id not in storage.items_db:
        raise HTTPException(404, "Позиция не найдена")
    
    db_item = storage.items_db[item_id]
    if item.name is not None: db_item["name"] = item.name
    if item.quantity is not None: db_item["quantity"] = item.quantity
    if item.unit_price is not None: db_item["unit_price"] = item.unit_price
    
    db_item["amount"] = db_item["quantity"] * db_item["unit_price"]
    recalculate(est["id"])
    return {"ok": True, "new_total": est["total_amount"]}

@router.delete("/events/{event_id}/estimate/items/{item_id}")
def delete_item(event_id: int, item_id: int):
    est = get_or_create_est(event_id)
    if est["status"] not in [EstimateStatus.DRAFT, EstimateStatus.PENDING]:
        raise HTTPException(400, "Смета утверждена, удаление запрещено")
        
    if item_id not in storage.items_db:
        raise HTTPException(404, "Позиция не найдена")
    
    del storage.items_db[item_id]
    recalculate(est["id"])
    return {"ok": True, "new_total": est["total_amount"]}

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

# ==================== ПЛАТЕЖИ И ВОЗВРАТЫ ====================

@router.get("/events/{event_id}/payments")
def get_payment_history(event_id: int):
    est = get_or_create_est(event_id)
    return [p for p in storage.payments_db.values() if p["estimate_id"] == est["id"]]

# НОВОЕ: Детальная история конкретного платежа
@router.get("/payments/{payment_id}/logs")
def get_payment_logs(payment_id: int):
    return [log for log in storage.payment_logs_db.values() if log["payment_id"] == payment_id]

@router.post("/events/{event_id}/payments")
def create_payment(event_id: int, pay: PaymentCreate):
    est = get_or_create_est(event_id)
    pay_id = storage.next_id("payment")
    storage.payments_db[pay_id] = {
        "id": pay_id, "estimate_id": est["id"], "amount": pay.amount, 
        "method": pay.method, "status": PaymentStatus.PENDING
    }
    log_payment_action(pay_id, "created", "none", PaymentStatus.PENDING)
    return {"ok": True, "payment_id": pay_id, "status": "pending"}

@router.post("/payments/{payment_id}/confirm")
def confirm_payment(payment_id: int):
    if payment_id not in storage.payments_db:
        raise HTTPException(404, "Платёж не найден")
    
    payment = storage.payments_db[payment_id]
    if payment["status"] != PaymentStatus.PENDING:
        raise HTTPException(400, f"Нельзя подтвердить платёж в статусе {payment['status']}")

    old_status = payment["status"]
    payment["status"] = PaymentStatus.CONFIRMED
    log_payment_action(payment_id, "confirmed", old_status, PaymentStatus.CONFIRMED)
    
    recalculate(payment["estimate_id"])
    est = storage.estimates_db[payment["estimate_id"]]
    return {"ok": True, "msg": "Платёж подтвержден", "remaining_debt": est["debt_amount"]}

# НОВОЕ: Возврат средств (Refund)
@router.post("/payments/{payment_id}/refund")
def refund_payment(payment_id: int):
    if payment_id not in storage.payments_db:
        raise HTTPException(404, "Платёж не найден")
    
    payment = storage.payments_db[payment_id]
    if payment["status"] != PaymentStatus.CONFIRMED:
        raise HTTPException(400, "Возврат возможен только для подтвержденных платежей")

    old_status = payment["status"]
    payment["status"] = PaymentStatus.REFUNDED
    log_payment_action(payment_id, "refunded", old_status, PaymentStatus.REFUNDED)
    
    recalculate(payment["estimate_id"])
    est = storage.estimates_db[payment["estimate_id"]]
    return {"ok": True, "msg": "Средства возвращены клиенту", "new_debt": est["debt_amount"]}