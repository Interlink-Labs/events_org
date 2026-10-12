from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estimate import Estimate, EstimateStatus, ItemType
from app.repositories.estimate_repo import EstimateRepository
from app.schemas.estimate import EstimateItemCreate, EstimateItemUpdate, AdditionalExpenseCreate


class EstimateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EstimateRepository(db)

    async def get_or_create(self, event_id: int) -> Estimate:
        est = await self.repo.get_by_event(event_id)
        if est is None:
            est = await self.repo.create(event_id)
            await self.db.commit()
            est = await self.repo.get_by_event(event_id)
        return est

    def _ensure_editable(self, est: Estimate) -> None:
        if est.status in (EstimateStatus.CLOSED, EstimateStatus.CANCELLED):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Смета в статусе '{est.status.value}' не может быть изменена",
            )

    async def add_item(self, event_id: int, payload: EstimateItemCreate) -> Estimate:
        est = await self.get_or_create(event_id)
        self._ensure_editable(est)

        amount = (payload.quantity * payload.unit_price).quantize(Decimal("0.01"))

        await self.repo.add_item(
            est,
            service_id=payload.service_id,
            contractor_id=payload.contractor_id,
            responsible_user_id=payload.responsible_user_id,
            name_snapshot=payload.name_snapshot or f"service#{payload.service_id}",
            unit=payload.unit,
            quantity=payload.quantity,
            unit_price=payload.unit_price,
            amount=amount,
            item_type=payload.item_type,
            comment=payload.comment,
        )
        await self.repo.recalculate(est)
        await self.db.commit()
        return await self.repo.get_by_event(event_id)

    async def update_item(self, event_id: int, item_id: int, payload: EstimateItemUpdate) -> Estimate:
        est = await self.get_or_create(event_id)
        self._ensure_editable(est)

        item = next((i for i in est.items if i.id == item_id), None)
        if item is None:
            raise HTTPException(status_code=404, detail="Позиция сметы не найдена")

        if payload.quantity is not None:
            item.quantity = payload.quantity
        if payload.unit_price is not None:
            item.unit_price = payload.unit_price
        if payload.comment is not None:
            item.comment = payload.comment

        item.amount = (item.quantity * item.unit_price).quantize(Decimal("0.01"))

        await self.repo.recalculate(est)
        await self.db.commit()
        return await self.repo.get_by_event(event_id)

    async def delete_item(self, event_id: int, item_id: int) -> Estimate:
        est = await self.get_or_create(event_id)
        self._ensure_editable(est)

        item = next((i for i in est.items if i.id == item_id), None)
        if item is None:
            raise HTTPException(status_code=404, detail="Позиция сметы не найдена")

        await self.db.delete(item)
        await self.db.flush()
        await self.repo.recalculate(est)
        await self.db.commit()
        return await self.repo.get_by_event(event_id)

    async def add_expense(
        self, event_id: int, payload: AdditionalExpenseCreate, user_id: int | None
    ) -> Estimate:
        est = await self.get_or_create(event_id)
        self._ensure_editable(est)

        await self.repo.add_expense(
            est, name=payload.name, amount=payload.amount,
            comment=payload.comment, created_by=user_id,
        )
        await self.repo.recalculate(est)
        await self.db.commit()
        return await self.repo.get_by_event(event_id)

    async def recalculate(self, event_id: int) -> Estimate:
        est = await self.get_or_create(event_id)
        await self.repo.recalculate(est)
        await self.db.commit()
        return await self.repo.get_by_event(event_id)