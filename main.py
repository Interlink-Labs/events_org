import traceback
from fastapi import FastAPI, HTTPException, Response, Cookie, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime, timedelta
import re
import cllients
from hashlib import sha256
from random import randint
from database import engine, Base
import models
import services_db
import events_db  

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interlink-Labs API")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================== СМЕТА И ОПЛАТА (модуль billing) ====================
from billing.router import router as billing_router
app.include_router(billing_router)


# ==================== УСЛУГИ (модуль services) ====================
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

@app.post("/api/v1/venues/create", tags=["Услуги"])
def create_venue_service(venue: VenuePackage):
    venue_id = services_db.write_venue(venue.name, venue.address, venue.capacity)
    return {"message": "Локация создана, базовые услуги добавлены", "venue_id": venue_id}

@app.get("/api/v1/venues/list", tags=["Услуги"])
def list_venues_service():
    return services_db.get_venues()

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

@app.post("/api/v1/services/base", tags=["Услуги"])
def add_base_services(venue_id: int):
    venue_or_404(venue_id)
    added = services_db.add_base_services(venue_id)
    return {"message": "Базовые услуги добавлены", "added": added}

@app.post("/api/v1/services/phone", tags=["Услуги"])
def set_service_phone(data: ServicePhonePackage):
    if services_db.update_service_phone(data.service_id, data.contact_phone):
        return {"message": "Номер телефона обновлён"}
    raise HTTPException(status_code=404, detail="Услуга не найдена")

@app.post("/api/v1/venues/phone", tags=["Услуги"])
def set_venue_phone(data: VenuePhonePackage):
    venue_or_404(data.venue_id)
    updated = services_db.update_venue_phone(data.venue_id, data.contact_phone)
    return {"message": "Номер телефона привязан к локации", "updated": updated}


#=========================== Модуль клиентов ============================
class Package(BaseModel):
    username: str
    password: str

fast_jwt = FastJWT(secret_key="not-secret-key-abcdefghijklmnopqrstuvwxyz")

@app.post("/api/v1/clients/registration")
def reg_client(user: Package, response: Response):
    try:
        username = user.username
        password = user.password
        
        if cllients.write_user(username, password):
            access_token = fast_jwt.create_access_token(
                user_id=username, expires_delta=timedelta(minutes=30)
            )
            refresh_token = fast_jwt.create_refresh_token(
                user_id=username, expires_delta=timedelta(minutes=30)
            )

            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,   # Важно для безопасности
                secure=True,     # Только для HTTPS
                samesite="lax"   # или "strict"
            )
            return {"access_token": access_token}

        else:
            return 'юзернейм занят'
    except Exception as e:
        print(e)

@app.post("/api/v1/clients/login")
def sign_client(user: Package):
    try:
        username = user.username
        password = user.password
        
        if cllients.validate_user(username, password):
            return 'Вы вошли!'
        else:
            return 'Неверный логин или пароль'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/client/get")
def get_client(username: str):
    try:
        return cllients.get_user(username)
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.put("/api/v1/clients/update")
def update_client(user: Package):
    try:
        username = user.username
        new_password = user.password
        
        if cllients.update_user(username, new_password):
            return 'Данные обновлены!'
        else:
            return 'Пользователь не найден'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.delete("/api/v1/clients/delete")
def delete_client(username: str):
    try:
        if cllients.delete_user(username):
            return 'Пользователь удален'
        else:
            return 'Пользователь не найден'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/refresh")
def refresh(new_tokens: dict = Depends(fast_jwt.refresh_token)):
    return new_tokens

@app.get("/protected", dependencies=[Depends(fast_jwt.auth_required)])
def protected_route():
    return {"message": "Доступ разрешён"}

# ==================== МОДУЛЬ МЕРОПРИЯТИЙ ====================

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

@app.get("/venues", response_model=List[VenueResponse], tags=["Мероприятия"])
def list_events_venues():
    return events_db.get_all_venues()

@app.get("/venues/free", response_model=List[VenueResponse], tags=["Мероприятия"])
def list_free_venues(date_str: date, participants: int = 1):
    return events_db.get_free_venues(str(date_str), participants)

@app.get("/venues/{venue_id}", response_model=VenueResponse, tags=["Мероприятия"])
def get_events_venue(venue_id: int):
    v = events_db.get_venue(venue_id)
    if not v:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    return v

@app.post("/venues", response_model=VenueResponse, status_code=status.HTTP_201_CREATED, tags=["Мероприятия"])
def create_events_venue(venue: VenueCreate):
    new_id = events_db.create_venue(venue.name, venue.address, venue.capacity, venue.description, venue.contact_phone)
    return events_db.get_venue(new_id)

@app.put("/venues/{venue_id}", response_model=VenueResponse, tags=["Мероприятия"])
def update_events_venue(venue_id: int, venue: VenueCreate):
    if not events_db.get_venue(venue_id):
        raise HTTPException(status_code=404, detail="Локация не найдена")
    ok = events_db.update_venue(venue_id, venue.name, venue.address, venue.capacity, venue.description, venue.contact_phone)
    if not ok:
        raise HTTPException(status_code=400, detail="Не удалось обновить локацию")
    return events_db.get_venue(venue_id)

@app.delete("/venues/{venue_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Мероприятия"])
def delete_events_venue(venue_id: int):
    if not events_db.get_venue(venue_id):
        raise HTTPException(status_code=404, detail="Локация не найдена")
    if not events_db.delete_venue(venue_id):
        raise HTTPException(status_code=400, detail="Нельзя удалить локацию, по которой есть активные брони")
    return None

@app.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED, tags=["Мероприятия"])
def create_event(event: EventCreate):
    ok, result = events_db.create_event(
        client_id=event.client_id, location_id=event.location_id, event_type=event.event_type,
        date_str=str(event.date), time_start=event.time_start, time_end=event.time_end,
        participants=event.participants, total_amount=event.total_amount, comment=event.comment,
        services=event.services, service_configs=event.service_configs,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=result)
    return events_db.get_event(result)

@app.get("/events", response_model=List[EventResponse], tags=["Мероприятия"])
def list_events(client_id: Optional[int] = None, status_filter: Optional[str] = None):
    return events_db.get_events(client_id, status_filter)

@app.get("/events/{event_id}", response_model=EventResponse, tags=["Мероприятия"])
def get_event(event_id: int):
    event = events_db.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event

@app.put("/events/{event_id}", response_model=EventResponse, tags=["Мероприятия"])
def update_event(event_id: int, payload: EventUpdate):
    if not events_db.get_event(event_id):
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    data = payload.model_dump(exclude_unset=True)
    if "date" in data:
        data["date"] = str(data["date"])
    if not events_db.update_event(event_id, data):
        raise HTTPException(status_code=400, detail="Не удалось обновить мероприятие")
    return events_db.get_event(event_id)

@app.put("/events/{event_id}/status", tags=["Мероприятия"])
def update_event_status(event_id: int, payload: StatusUpdate):
    if payload.new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Допустимые статусы: {sorted(VALID_STATUSES)}")
    if not events_db.update_event_status(event_id, payload.new_status):
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return {"message": "Статус обновлён", "event_id": event_id, "status": payload.new_status}

@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Мероприятия"])
def delete_event(event_id: int):
    if not events_db.delete_event(event_id):
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return None

@app.get("/")
def root():
    return {"message": "API работает. Открой /docs"}

