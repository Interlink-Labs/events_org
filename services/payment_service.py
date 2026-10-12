from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estimate import PaymentStatus
from app.repositories.estimate_repo import EstimateRepository
from app.repositories.payment_repo import PaymentRepository
from app.schemas.payment import PaymentCreate


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payments = PaymentRepository(db)
        self.estimates = EstimateRepository(db)

    async def list_for_event(self, event_id: int):
        return await self.payments.list_by_event(event_id)

    async def create(self, event_id: int, payload: PaymentCreate, user_id: int):
        est = await self.estimates.get_by_event(event_id)
        if est is None:
            raise HTTPException(status_code=404, detail="Смета не найдена")

        payment = await self.payments.create(
            event_id=event_id,
            estimate_id=est.id,
            amount=payload.amount,
            currency=est.currency,
            method=payload.method,
            paid_at=payload.paid_at or datetime.now(timezone.utc),
            comment=payload.comment,
            created_by=user_id,
            status=PaymentStatus.PENDING,
        )
        await self.db.commit()
        return payment

    async def confirm(self, payment_id: int, user_id: int):
        p = await self.payments.get(payment_id)
        if p is None:
            raise HTTPException(status_code=404, detail="Платёж не найден")
        if p.status != PaymentStatus.PENDING:
            raise HTTPException(status_code=409, detail=f"Нельзя подтвердить платёж в статусе {p.status.value}")

        await self.payments.change_status(p, PaymentStatus.CONFIRMED, user_id)
        p.confirmed_by = user_id
        p.confirmed_at = datetime.now(timezone.utc)

        est = await self.estimates.get_by_id(p.estimate_id)
        await self.estimates.recalculate(est)
        await self.db.commit()
        return p

    async def cancel(self, payment_id: int, user_id: int, comment: str | None = None):
        p = await self.payments.get(payment_id)
        if p is None:
            raise HTTPException(status_code=404, detail="Платёж не найден")
        if p.status in (PaymentStatus.CANCELLED, PaymentStatus.REFUNDED):
            raise HTTPException(status_code=409, detail="Платёж уже отменён/возвращён")

        await self.payments.change_status(p, PaymentStatus.CANCELLED, user_id, comment)

        est = await self.estimates.get_by_id(p.estimate_id)
        await self.estimates.recalculate(est)
        await self.db.commit()
        return p

    async def refund(self, payment_id: int, user_id: int, comment: str | None = None):
        p = await self.payments.get(payment_id)
        if p is None:
            raise HTTPException(status_code=404, detail="Платёж не найден")
        if p.status != PaymentStatus.CONFIRMED:
            raise HTTPException(status_code=409, detail="Возврат возможен только по подтверждённому платежу")

        await self.payments.change_status(p, PaymentStatus.REFUNDED, user_id, comment)

        est = await self.estimates.get_by_id(p.estimate_id)
        await self.estimates.recalculate(est)
        await self.db.commit()
        return p