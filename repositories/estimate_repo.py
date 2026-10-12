from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.estimate import (
    Estimate, EstimateItem, AdditionalExpense, Payment, PaymentStatus,
)


class EstimateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_event(self, event_id: int) -> Estimate | None:
        stmt = (
            select(Estimate)
            .where(Estimate.event_id == event_id)
            .options(selectinload(Estimate.items), selectinload(Estimate.expenses))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, estimate_id: int) -> Estimate | None:
        stmt = (
            select(Estimate)
            .where(Estimate.id == estimate_id)
            .options(selectinload(Estimate.items), selectinload(Estimate.expenses))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def create(self, event_id: int) -> Estimate:
        est = Estimate(event_id=event_id)
        self.db.add(est)
        await self.db.flush()
        return est

    async def add_item(self, estimate: Estimate, **data) -> EstimateItem:
        item = EstimateItem(estimate_id=estimate.id, **data)
        self.db.add(item)
        await self.db.flush()
        return item

    async def add_expense(self, estimate: Estimate, **data) -> AdditionalExpense:
        exp = AdditionalExpense(estimate_id=estimate.id, **data)
        self.db.add(exp)
        await self.db.flush()
        return exp

    async def recalculate(self, estimate: Estimate) -> Estimate:
        """Пересчёт всех финансовых полей сметы."""
        await self.db.refresh(estimate, attribute_names=["items", "expenses"])

        services_total = sum(
            (i.amount for i in estimate.items if i.item_type.value == "service"),
            Decimal("0.00"),
        )
        discount_total = sum(
            (i.amount for i in estimate.items if i.item_type.value == "discount"),
            Decimal("0.00"),
        )
        expenses_total = sum((e.amount for e in estimate.expenses), Decimal("0.00"))

        # подтверждённые платежи
        pay_stmt = select(Payment).where(
            Payment.estimate_id == estimate.id,
            Payment.status == PaymentStatus.CONFIRMED,
        )
        payments = (await self.db.execute(pay_stmt)).scalars().all()
        paid_amount = sum((p.amount for p in payments), Decimal("0.00"))

        total = services_total + expenses_total - discount_total
        debt = total - paid_amount
        overpay = -debt if debt < 0 else Decimal("0.00")

        estimate.services_total = services_total
        estimate.discount_total = discount_total
        estimate.expenses_total = expenses_total
        estimate.total_amount = total
        estimate.paid_amount = paid_amount
        estimate.debt_amount = debt if debt > 0 else Decimal("0.00")
        estimate.overpayment_amount = overpay

        await self.db.flush()
        return estimate