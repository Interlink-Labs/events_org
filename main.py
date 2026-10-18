from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import events_db


# ==================== SCHEMAS ====================
class VenuePackage(BaseModel):
    name: str
    address: str
    capacity: int
    description: Optional[str] = None


class EventPackage(BaseModel):
    title: str
    date: str  # "YYYY-MM-DDTHH:MM:SS"
    location: str
    participants_count: int
    description: Optional[str] = None
    venue_id: Optional[int] = None


class EventUpdatePackage(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    participants_count: Optional[int] = None
    description: Optional[str] = None
    venue_id: Optional[int] = None


app = FastAPI()


# ==================== VENUES ====================
@app.post("/api/v1/venues/create")
def create_venue(v: VenuePackage):
    venue_id = events_db.create_venue(v.name, v.address, v.capacity, v.description)
    return {"ok": True, "venue_id": venue_id}


@app.get("/api/v1/venues")
def get_venues():
    return events_db.list_venues()


@app.get("/api/v1/venues/{venue_id}")
def get_venue(venue_id: int):
    v = events_db.get_venue(venue_id)
    return v if v else {"error": "Площадка не найдена"}


# ==================== EVENTS (CRUD) ====================
@app.post("/api/v1/events/create")
def create_event(e: EventPackage):
    event_id = events_db.create_event(
        title=e.title,
        date=e.date,
        location=e.location,
        participants_count=e.participants_count,
        description=e.description,
        venue_id=e.venue_id
    )

    # Автоподбор + автобронь, если площадка не задана
    if e.venue_id is None:
        suitable = events_db.find_suitable_venues(e.participants_count, e.date)
        if not suitable:
            events_db.delete_event(event_id)
            return {"ok": False, "error": "Нет свободных подходящих площадок на эту дату"}

        venue = suitable[0]
        result = events_db.book_venue(event_id, venue["id"])
        if not result["ok"]:
            events_db.delete_event(event_id)
            return {"ok": False, "error": result["error"]}

        return {
            "ok": True,
            "event_id": event_id,
            "booked_venue": venue
        }

    # Если площадка задана — бронируем её
    result = events_db.book_venue(event_id, e.venue_id)
    if not result["ok"]:
        events_db.delete_event(event_id)
        return {"ok": False, "error": result["error"]}

    return {"ok": True, "event_id": event_id, "booking_id": result["booking_id"]}


@app.get("/api/v1/events")
def get_events():
    return events_db.list_events()


@app.get("/api/v1/events/{event_id}")
def get_event(event_id: int):
    e = events_db.get_event(event_id)
    return e if e else {"error": "Мероприятие не найдено"}


@app.post("/api/v1/events/{event_id}/update")
def update_event(event_id: int, e: EventUpdatePackage):
    ok = events_db.update_event(event_id, **e.model_dump(exclude_unset=True))
    return {"ok": ok, "msg": "Обновлено" if ok else "Мероприятие не найдено"}


@app.post("/api/v1/events/{event_id}/delete")
def delete_event(event_id: int):
    ok = events_db.delete_event(event_id)
    return {"ok": ok, "msg": "Удалено" if ok else "Мероприятие не найдено"}


# ==================== ПОДБОР ПЛОЩАДКИ ====================
@app.get("/api/v1/venues/suitable")
def suitable_venues(participants: int, event_date: str):
    return events_db.find_suitable_venues(participants, event_date)


# ==================== БРОНИРОВАНИЕ ====================
@app.post("/api/v1/events/{event_id}/book")
def book_event(event_id: int, venue_id: int):
    return events_db.book_venue(event_id, venue_id)


@app.get("/api/v1/events/{event_id}/booking")
def get_booking(event_id: int):
    b = events_db.get_booking(event_id)
    return b if b else {"error": "Брони нет"}
import uvicorn
from fastapi import FastAPI

from clients.Testun import client_bp

app = FastAPI()

app.include_router(client_bp)


@app.get('/')
def root():
    return {"message": "API работает. Открой /docs"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
