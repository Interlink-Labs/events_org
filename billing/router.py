from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from decimal import Decimal

from database import get_db
import models
from models import EstimateStatus, PaymentStatus, ItemType
from billing.schemas import (
    ItemCreate, ItemUpdate, PaymentCreate, ExpenseCreate, EstimateStatusUpdate
)

router = APIRouter(prefix="/api/v1/billing", tags=["Смета и оплата"])

def get_or_create_est(event_id: int, db: Session):
    est = db.query(models.Estimate).filter(models.Estimate.event_id == event_id).first()
    if not est:
        est = models.Estimate(event_id=event_id)
        db.add(est)
        db.commit()
        db.refresh(est)
    return est

def recalculate(est_id: int, db: Session):
    est = db.query(models.Estimate).filter(models.Estimate.id == est_id).first()
    items = db.query(models.EstimateItem).filter(models.EstimateItem.estimate_id == est_id).all()
    expenses = db.query(models.AdditionalExpense).filter(models.AdditionalExpense.estimate_id == est_id).all()
    payments = db.query(models.Payment).filter(
        models.Payment.estimate_id == est_id, 
        models.Payment.status == PaymentStatus.CONFIRMED
    ).all()
    
    services_total = sum((i.amount for i in items if i.item_type == ItemType.SERVICE), Decimal("0.00"))
    discounts = sum((i.amount for i in items if i.item_type == ItemType.DISCOUNT), Decimal("0.00"))
    expenses_total = sum((e.amount for e in expenses), Decimal("0.00"))
    paid = sum((p.amount for p in payments), Decimal("0.00"))
    
    total = services_total + expenses_total - discounts
    
    est.services_total = services_total
    est.expenses_total = expenses_total
    est.total_amount = total
    est.paid_amount = paid
    
    if total > paid:
        est.debt_amount = total - paid
        est.overpayment_amount = Decimal("0.00")
    elif paid > total:
        est.debt_amount = Decimal("0.00")
        est.overpayment_amount = paid - total
    else:
        est.debt_amount = Decimal("0.00")
        est.overpayment_amount = Decimal("0.00")
        
    if est.status == EstimateStatus.APPROVED and est.debt_amount == Decimal("0.00") and total > Decimal("0.00"):
        est.status = EstimateStatus.PAID
        
    db.commit()

@router.get("/events/{event_id}/estimate")
def get_estimate(event_id: int, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    items = db.query(models.EstimateItem).filter(models.EstimateItem.estimate_id == est.id).all()
    expenses = db.query(models.AdditionalExpense).filter(models.AdditionalExpense.estimate_id == est.id).all()
    return {"estimate": est, "items": items, "expenses": expenses}

@router.patch("/events/{event_id}/estimate/status")
def update_estimate_status(event_id: int, payload: EstimateStatusUpdate, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    if est.status in [EstimateStatus.CLOSED, EstimateStatus.CANCELLED]:
        raise HTTPException(400, "Нельзя изменить статус закрытой сметы")
    est.status = payload.status
    db.commit()
    return {"ok": True, "new_status": est.status}

@router.post("/events/{event_id}/estimate/items")
def add_item(event_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    if est.status not in [EstimateStatus.DRAFT, EstimateStatus.PENDING]:
        raise HTTPException(400, "Нельзя менять утвержденную смету")
    
    amount = item.quantity * item.unit_price
    db_item = models.EstimateItem(
        estimate_id=est.id, name=item.name, quantity=item.quantity, 
        unit_price=item.unit_price, amount=amount, item_type=item.item_type
    )
    db.add(db_item)
    db.commit()
    recalculate(est.id, db)
    return {"ok": True, "item_id": db_item.id, "total": est.total_amount}

@router.patch("/events/{event_id}/estimate/items/{item_id}")
def update_item(event_id: int, item_id: int, item: ItemUpdate, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    if est.status not in [EstimateStatus.DRAFT, EstimateStatus.PENDING]:
        raise HTTPException(400, "Смета утверждена, изменения запрещены")
        
    db_item = db.query(models.EstimateItem).filter(models.EstimateItem.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Позиция не найдена")
        
    if item.name is not None: db_item.name = item.name
    if item.quantity is not None: db_item.quantity = item.quantity
    if item.unit_price is not None: db_item.unit_price = item.unit_price
    
    db_item.amount = db_item.quantity * db_item.unit_price
    db.commit()
    recalculate(est.id, db)
    return {"ok": True, "new_total": est.total_amount}

@router.delete("/events/{event_id}/estimate/items/{item_id}")
def delete_item(event_id: int, item_id: int, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    if est.status not in [EstimateStatus.DRAFT, EstimateStatus.PENDING]:
        raise HTTPException(400, "Смета утверждена, удаление запрещено")
        
    db_item = db.query(models.EstimateItem).filter(models.EstimateItem.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Позиция не найдена")
        
    db.delete(db_item)
    db.commit()
    recalculate(est.id, db)
    return {"ok": True, "new_total": est.total_amount}

@router.post("/events/{event_id}/estimate/expenses")
def add_expense(event_id: int, exp: ExpenseCreate, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    db_exp = models.AdditionalExpense(estimate_id=est.id, name=exp.name, amount=exp.amount)
    db.add(db_exp)
    db.commit()
    recalculate(est.id, db)
    return {"ok": True, "expense_id": db_exp.id, "total": est.total_amount}

@router.delete("/events/{event_id}/estimate/expenses/{expense_id}")
def delete_expense(event_id: int, expense_id: int, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    if est.status not in [EstimateStatus.DRAFT, EstimateStatus.PENDING]:
        raise HTTPException(400, "Смета утверждена, удаление запрещено")
        
    db_exp = db.query(models.AdditionalExpense).filter(models.AdditionalExpense.id == expense_id).first()
    if not db_exp:
        raise HTTPException(404, "Расход не найден")
        
    db.delete(db_exp)
    db.commit()
    recalculate(est.id, db)
    return {"ok": True, "new_total": est.total_amount}

@router.get("/events/{event_id}/payments")
def get_payment_history(event_id: int, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    return db.query(models.Payment).filter(models.Payment.estimate_id == est.id).all()

@router.post("/events/{event_id}/payments")
def create_payment(event_id: int, pay: PaymentCreate, db: Session = Depends(get_db)):
    est = get_or_create_est(event_id, db)
    db_pay = models.Payment(estimate_id=est.id, amount=pay.amount, method=pay.method)
    db.add(db_pay)
    db.commit()
    db.refresh(db_pay)
    
    log = models.PaymentLog(payment_id=db_pay.id, action="created", old_status="none", new_status="pending")
    db.add(log)
    db.commit()
    return {"ok": True, "payment_id": db_pay.id, "status": "pending"}

@router.post("/payments/{payment_id}/confirm")
def confirm_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(404, "Платёж не найден")
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(400, f"Нельзя подтвердить платёж в статусе {payment.status}")
    
    old_status = payment.status
    payment.status = PaymentStatus.CONFIRMED
    db.commit()
    
    log = models.PaymentLog(payment_id=payment.id, action="confirmed", old_status=str(old_status), new_status="confirmed")
    db.add(log)
    db.commit()
    
    recalculate(payment.estimate_id, db)
    return {"ok": True, "msg": "Платёж подтвержден"}

@router.post("/payments/{payment_id}/refund")
def refund_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(404, "Платёж не найден")
    if payment.status != PaymentStatus.CONFIRMED:
        raise HTTPException(400, "Возврат возможен только для подтвержденных платежей")
    
    old_status = payment.status
    payment.status = PaymentStatus.REFUNDED
    db.commit()
    
    log = models.PaymentLog(payment_id=payment.id, action="refunded", old_status=str(old_status), new_status="refunded")
    db.add(log)
    db.commit()
    
    recalculate(payment.estimate_id, db)
    return {"ok": True, "msg": "Средства возвращены клиенту"}

@router.get("/payments/{payment_id}/logs")
def get_payment_logs(payment_id: int, db: Session = Depends(get_db)):
    return db.query(models.PaymentLog).filter(models.PaymentLog.payment_id == payment_id).all()