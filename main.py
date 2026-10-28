from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
import database

app = FastAPI(title="Events API")


class EventBase(BaseModel):
    client_id: int
    location_id: int
    event_type: str
    date: date
    time_start: str
    time_end: str
    participants: int
    total_amount: float
    comment: Optional[str] = ""
    services: List[int] = []
    service_configs: dict = {}

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int
    status: str
    created_at: datetime

class StatusUpdate(BaseModel):
    new_status: str



@app.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate):
    
    event_data = event.model_dump()
    event_data["date"] = str(event_data["date"]) 

    # Вызываем функцию из database.py
    result = database.create_event_db(event_data)
    
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])


    created_events = database.get_events_db()
    created = next((e for e in created_events if e["id"] == result["event_id"]), None)
    return created


@app.get("/", response_model=List[EventResponse])
async def get_events(client_id: Optional[int] = None, status_filter: Optional[str] = None):
    return database.get_events_db(client_id, status_filter)


@app.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int):
    events = database.get_events_db()
    event = next((e for e in events if e["id"] == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event


@app.put("/{event_id}/status")
async def update_event_status(event_id: int, payload: StatusUpdate):
    valid_statuses = ["pending", "approved", "rejected", "completed"]
    if payload.new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Неверный статус")
    
    success = database.update_status_db(event_id, payload.new_status)
    if not success:
         raise HTTPException(status_code=404, detail="Мероприятие не найдено")
         
    return {"message": "Статус обновлен", "event_id": event_id, "status": payload.new_status}


@app.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int):
    success = database.delete_event_db(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return None