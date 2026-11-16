from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/ping")
def ping():
    return {"module": "auth", "status": "ok"}