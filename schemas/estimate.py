from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_manager
from app.core.database import get_db
from app.schemas.estimate import (
    EstimateRead, EstimateItemCreate, EstimateItemUpdate, AdditionalExpenseCreate,
)
from app.services.estimate_service import EstimateService

router = APIRouter(prefix="/api/events/{event_id}/estimate", tags=["estimate"])


@router.get("", response_model=EstimateRead)
async def get_estimate(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await EstimateService(db).get_or_create(event_id)


@router.post("/items", response_model=EstimateRead)
async def add_item(
    event_id: int,
    payload: EstimateItemCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await EstimateService(db).add_item(event_id, payload)


@router.patch("/items/{item_id}", response_model=EstimateRead)
async def update_item(
    event_id: int,
    item_id: int,
    payload: EstimateItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await EstimateService(db).update_item(event_id, item_id, payload)


@router.delete("/items/{item_id}", response_model=EstimateRead)
async def delete_item(
    event_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await EstimateService(db).delete_item(event_id, item_id)


@router.post("/expenses", response_model=EstimateRead)
async def add_expense(
    event_id: int,
    payload: AdditionalExpenseCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_manager),
):
    return await EstimateService(db).add_expense(event_id, payload, user["id"])


@router.post("/recalculate", response_model=EstimateRead)
async def recalculate(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_manager),
):
    return await EstimateService(db).recalculate(event_id)