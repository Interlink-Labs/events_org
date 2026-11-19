<<<<<<< HEAD
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
=======
import traceback
from fastapi import FastAPI, HTTPException, Response, Cookie
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re
import clients
from hashlib import sha256
from random import randint
from database import engine, Base
import models
import services_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interlink-Labs API")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================== СМЕТА И ОПЛАТА (модуль billing, без изменений) ====================
from billing.router import router as billing_router
app.include_router(billing_router)


# ==================== УСЛУГИ (модуль services, SQLite: services_db.py) ====================
PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{5,20}$")


def check_phone(v: str) -> str:
    v = v.strip()
    if v != services_db.DEFAULT_PHONE and not PHONE_RE.match(v):
        raise ValueError("Некорректный номер телефона")
    return v


class VenuePackage(BaseModel):
    name: str = Field(min_length=1)
    address: str = Field(min_length=1)
    capacity: int = Field(gt=0)


class ServicePackage(BaseModel):
    venue_id: int
    name: str = Field(min_length=1)
    description: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    contact_phone: str = services_db.DEFAULT_PHONE

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        return check_phone(v)


class ServiceUpdatePackage(BaseModel):
    service_id: int
    name: str = Field(min_length=1)
    description: Optional[str] = None
    price: float = Field(ge=0)
    contact_phone: str = services_db.DEFAULT_PHONE

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        return check_phone(v)


class ServicePhonePackage(BaseModel):
    service_id: int
    contact_phone: str

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        return check_phone(v)


class VenuePhonePackage(BaseModel):
    venue_id: int
    contact_phone: str

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        return check_phone(v)


def venue_or_404(venue_id: int):
    if not services_db.check_venue(venue_id):
        raise HTTPException(status_code=404, detail="Локация не найдена")


# ----- локации -----
@app.post("/api/v1/venues/create", tags=["Услуги"])
def create_venue(venue: VenuePackage):
    """Создаёт локацию, базовые услуги добавляются автоматически (п. 13)"""
    venue_id = services_db.write_venue(venue.name, venue.address, venue.capacity)
    return {"message": "Локация создана, базовые услуги добавлены", "venue_id": venue_id}


@app.get("/api/v1/venues/list", tags=["Услуги"])
def list_venues():
    return services_db.get_venues()


# ----- услуги: CRUD (п. 12) -----
@app.post("/api/v1/services/create", tags=["Услуги"])
def create_service(service: ServicePackage):
    venue_or_404(service.venue_id)
    service_id = services_db.write_service(
        service.venue_id, service.name, service.description, service.price, service.contact_phone
    )
    if service_id is None:
        raise HTTPException(status_code=409, detail="У этой локации уже есть услуга с таким названием")
    return {"message": "Услуга создана", "service_id": service_id}


@app.post("/api/v1/services/get", tags=["Услуги"])
def get_service(service_id: int):
    service = services_db.get_service(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return service


@app.get("/api/v1/services/list", tags=["Услуги"])
def list_services(venue_id: Optional[int] = None):
    """Все услуги или услуги одной локации"""
    if venue_id is not None:
        venue_or_404(venue_id)
    return services_db.get_services(venue_id)


@app.post("/api/v1/services/update", tags=["Услуги"])
def update_service(service: ServiceUpdatePackage):
    result = services_db.update_service(
        service.service_id, service.name, service.description, service.price, service.contact_phone
    )
    if result is None:
        raise HTTPException(status_code=409, detail="У этой локации уже есть услуга с таким названием")
    if not result:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return {"message": "Услуга обновлена", "service": services_db.get_service(service.service_id)}


@app.post("/api/v1/services/delete", tags=["Услуги"])
def delete_service(service_id: int):
    if services_db.delete_service(service_id):
        return {"message": "Услуга удалена"}
    raise HTTPException(status_code=404, detail="Услуга не найдена")


# ----- базовые услуги (п. 13) -----
@app.post("/api/v1/services/base", tags=["Услуги"])
def add_base_services(venue_id: int):
    """Вернуть локации базовые услуги, если какие-то из них удалили"""
    venue_or_404(venue_id)
    added = services_db.add_base_services(venue_id)
    return {"message": "Базовые услуги добавлены", "added": added}


# ----- телефон ответственного (п. 14) -----
@app.post("/api/v1/services/phone", tags=["Услуги"])
def set_service_phone(data: ServicePhonePackage):
    """Телефон ответственного за одну услугу"""
    if services_db.update_service_phone(data.service_id, data.contact_phone):
        return {"message": "Номер телефона обновлён"}
    raise HTTPException(status_code=404, detail="Услуга не найдена")


@app.post("/api/v1/venues/phone", tags=["Услуги"])
def set_venue_phone(data: VenuePhonePackage):
    """Привязка к локации номера ответственного лица: ставится всем услугам локации"""
    venue_or_404(data.venue_id)
    updated = services_db.update_venue_phone(data.venue_id, data.contact_phone)
    return {"message": "Номер телефона привязан к локации", "updated": updated}


@app.get("/")
def root():
    return {"message": "API работает. Открой /docs"}
 
#=========================== Модуль клиентов ============================
class Package(BaseModel):
    username: str
    password: str

@app.post("/api/v1/clients/reg")
def reg_client(user: Package):
    try:
        username = user.username
        password = user.password
        
        if clients.write_user(username, password):
            return 'пользователь успешно зарегистрирован!'
        else:
            return 'юзернейм занят'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/clients/sign-in")
def sign_client(user: Package):
    try:
        username = user.username
        password = user.password
        
        if clients.validate_user(username, password):
            return 'Вы вошли!'
        else:
            return 'Неверный логин или пароль'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/clients/get")
def get_client(username: str):
    try:
        return clients.get_user(username)
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/clients/update")
def update_client(user: Package):
    try:
        username = user.username
        new_password = user.password
        
        if clients.update_user(username, new_password):
            return 'Данные обновлены!'
        else:
            return 'Пользователь не найден'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/clients/delete")
def delete_client(username: str):
    try:
        if clients.delete_user(username):
            return 'Пользователь удален'
        else:
            return 'Пользователь не найден'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.get("/api/v1/set-cookie")
def set_cookie(username, response: Response):
    try:
        value = str(randint(1, 1000000000))
        access_token = clients.hash_string(value)
        response.set_cookie(
            key="access_token", 
            value=value, 
            httponly=True,
            max_age=900,
            samesite="lax"
        )

        value = str(randint(1, 1000000000))
        refresh_token = clients.hash_string(value)
        response.set_cookie(
            key="refresh_token", 
            value=value, 
            httponly=True,
            max_age=86400,
            samesite="lax"
        )

        clients.write_cookie(access_token, refresh_token, username)
        return {"message": "Куки успешно установлены!"}
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.get('/api/v1/check-cookie')
def check_cookie(username, access_token: str = Cookie('1'), refresh_token: str = Cookie('1')):
    try:
        return clients.get_tokens(username, access_token, refresh_token)
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())
>>>>>>> b2d60f55fe4ad39a0b74e57e744db6644a636a6e
