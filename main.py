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
