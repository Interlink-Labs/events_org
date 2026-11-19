from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
import events_db

app = FastAPI(title="Events API")


# ==================== СХЕМЫ PYDANTIC ====================

class VenueBase(BaseModel):
    name: str
    address: str
    capacity: int = Field(gt=0)
    description: Optional[str] = ""
    contact_phone: Optional[str] = ""


class VenueCreate(VenueBase):
    pass


class VenueResponse(VenueBase):
    id: int


class EventBase(BaseModel):
    client_id: int
    location_id: int
    event_type: str
    date: date
    time_start: str
    time_end: str
    participants: int = Field(gt=0)
    total_amount: float = Field(ge=0)
    comment: Optional[str] = ""
    services: List[int] = Field(default_factory=list)
    service_configs: dict = Field(default_factory=dict)


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    """Для PUT /events/{id} — все поля опциональны."""
    event_type: Optional[str] = None
    date: Optional[date] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    participants: Optional[int] = Field(default=None, gt=0)
    total_amount: Optional[float] = Field(default=None, ge=0)
    comment: Optional[str] = None
    services: Optional[List[int]] = None
    service_configs: Optional[dict] = None


class EventResponse(EventBase):
    id: int
    status: str
    created_at: datetime


class StatusUpdate(BaseModel):
    new_status: str


VALID_STATUSES = {"pending", "approved", "rejected", "completed"}


# ==================== ЛОКАЦИИ ====================

@app.get("/venues", response_model=List[VenueResponse])
def list_venues():
    return events_db.get_all_venues()


@app.get("/venues/free", response_model=List[VenueResponse])
def list_free_venues(date_str: date, participants: int = 1):
    """Свободные локации подходящей вместимости на указанную дату (п.3, п.10 ТЗ)."""
    return events_db.get_free_venues(str(date_str), participants)


@app.get("/venues/{venue_id}", response_model=VenueResponse)
def get_venue(venue_id: int):
    v = events_db.get_venue(venue_id)
    if not v:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    return v


@app.post("/venues", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
def create_venue(venue: VenueCreate):
    new_id = events_db.create_venue(
        venue.name, venue.address, venue.capacity,
        venue.description, venue.contact_phone,
    )
    return events_db.get_venue(new_id)


@app.put("/venues/{venue_id}", response_model=VenueResponse)
def update_venue(venue_id: int, venue: VenueCreate):
    if not events_db.get_venue(venue_id):
        raise HTTPException(status_code=404, detail="Локация не найдена")
    ok = events_db.update_venue(
        venue_id, venue.name, venue.address, venue.capacity,
        venue.description, venue.contact_phone,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Не удалось обновить локацию")
    return events_db.get_venue(venue_id)


@app.delete("/venues/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(venue_id: int):
    if not events_db.get_venue(venue_id):
        raise HTTPException(status_code=404, detail="Локация не найдена")
    if not events_db.delete_venue(venue_id):
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить локацию, по которой есть активные брони",
        )
    return None


# ==================== МЕРОПРИЯТИЯ ====================

@app.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate):
    ok, result = events_db.create_event(
        client_id=event.client_id,
        location_id=event.location_id,
        event_type=event.event_type,
        date_str=str(event.date),
        time_start=event.time_start,
        time_end=event.time_end,
        participants=event.participants,
        total_amount=event.total_amount,
        comment=event.comment,
        services=event.services,
        service_configs=event.service_configs,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=result)
    return events_db.get_event(result)


@app.get("/events", response_model=List[EventResponse])
def list_events(client_id: Optional[int] = None, status_filter: Optional[str] = None):
    return events_db.get_events(client_id, status_filter)


@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int):
    event = events_db.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event


@app.put("/events/{event_id}", response_model=EventResponse)
def update_event(event_id: int, payload: EventUpdate):
    if not events_db.get_event(event_id):
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    data = payload.model_dump(exclude_unset=True)
    if "date" in data:
        data["date"] = str(data["date"])
    if not events_db.update_event(event_id, data):
        raise HTTPException(status_code=400, detail="Не удалось обновить мероприятие")
    return events_db.get_event(event_id)


@app.put("/events/{event_id}/status")
def update_event_status(event_id: int, payload: StatusUpdate):
    if payload.new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Допустимые статусы: {sorted(VALID_STATUSES)}",
        )
    if not events_db.update_event_status(event_id, payload.new_status):
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return {"message": "Статус обновлён", "event_id": event_id, "status": payload.new_status}


@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int):
    if not events_db.delete_event(event_id):
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return None