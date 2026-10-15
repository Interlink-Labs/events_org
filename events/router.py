from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/events", tags=["events"])

@router.get("/ping")
def ping():
    return {"module": "events", "status": "ok"}