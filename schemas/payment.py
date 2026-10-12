from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_manager
from app.core.database import get_db
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/events/{event_id}/payments", tags=["payments"])


@router.get("", response_model=list[PaymentRead])
async def list_payments(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await PaymentService(db).list_for_event(event_id)


@router.post("", response_model=PaymentRead)
async def create_payment(
    event_id: int,
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_manager),
):
    return await PaymentService(db).create(event_id, payload, user["id"])


@router.patch("/{payment_id}/confirm", response_model=PaymentRead)
async def confirm_payment(
    event_id: int,
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_manager),
):
    return await PaymentService(db).confirm(payment_id, user["id"])


@router.patch("/{payment_id}/cancel", response_model=PaymentRead)
async def cancel_payment(
    event_id: int,
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_manager),
):
    return await PaymentService(db).cancel(payment_id, user["id"])


@router.patch("/{payment_id}/refund", response_model=PaymentRead)
async def refund_payment(
    event_id: int,
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_manager),
):
    return await PaymentService(db).refund(payment_id, user["id"])