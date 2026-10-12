from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.estimate import Payment, PaymentStatus, PaymentStatusLog


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_event(self, event_id: int) -> list[Payment]:
        stmt = select(Payment).where(Payment.event_id == event_id).order_by(Payment.created_at.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def get(self, payment_id: int) -> Payment | None:
        return await self.db.get(Payment, payment_id)

    async def create(self, **data) -> Payment:
        p = Payment(**data)
        self.db.add(p)
        await self.db.flush()
        return p

    async def change_status(
        self,
        payment: Payment,
        new_status: PaymentStatus,
        user_id: int | None,
        comment: str | None = None,
    ) -> Payment:
        log = PaymentStatusLog(
            payment_id=payment.id,
            old_status=payment.status,
            new_status=new_status,
            changed_by=user_id,
            comment=comment,
        )
        self.db.add(log)
        payment.status = new_status
        await self.db.flush()
        return payment