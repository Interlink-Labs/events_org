from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re
import services_db


PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{5,20}$")


def check_phone(v: str) -> str:
    v = v.strip()
    if v != services_db.DEFAULT_PHONE and not PHONE_RE.match(v):
        raise ValueError("Некорректный номер телефона")
    return v


# ==================== PYDANTIC MODELS ====================
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


app = FastAPI(title="Interlink-Labs: модуль «Услуги»")


def venue_or_404(venue_id: int):
    if not services_db.check_venue(venue_id):
        raise HTTPException(status_code=404, detail="Локация не найдена")


# ==================== ЛОКАЦИИ ====================
@app.post("/api/v1/venues/create")
def create_venue(venue: VenuePackage):
    """Создаёт локацию, базовые услуги добавляются автоматически (п. 13)"""
    venue_id = services_db.write_venue(venue.name, venue.address, venue.capacity)
    return {"message": "Локация создана, базовые услуги добавлены", "venue_id": venue_id}


@app.get("/api/v1/venues/list")
def list_venues():
    return services_db.get_venues()


# ==================== УСЛУГИ: CRUD (п. 12) ====================
@app.post("/api/v1/services/create")
def create_service(service: ServicePackage):
    venue_or_404(service.venue_id)
    service_id = services_db.write_service(
        service.venue_id, service.name, service.description, service.price, service.contact_phone
    )
    if service_id is None:
        raise HTTPException(status_code=409, detail="У этой локации уже есть услуга с таким названием")
    return {"message": "Услуга создана", "service_id": service_id}


@app.post("/api/v1/services/get")
def get_service(service_id: int):
    service = services_db.get_service(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return service


@app.get("/api/v1/services/list")
def list_services(venue_id: Optional[int] = None):
    """Все услуги или услуги одной локации"""
    if venue_id is not None:
        venue_or_404(venue_id)
    return services_db.get_services(venue_id)


@app.post("/api/v1/services/update")
def update_service(service: ServiceUpdatePackage):
    result = services_db.update_service(
        service.service_id, service.name, service.description, service.price, service.contact_phone
    )
    if result is None:
        raise HTTPException(status_code=409, detail="У этой локации уже есть услуга с таким названием")
    if not result:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return {"message": "Услуга обновлена", "service": services_db.get_service(service.service_id)}


@app.post("/api/v1/services/delete")
def delete_service(service_id: int):
    if services_db.delete_service(service_id):
        return {"message": "Услуга удалена"}
    raise HTTPException(status_code=404, detail="Услуга не найдена")


# ==================== БАЗОВЫЕ УСЛУГИ (п. 13) ====================
@app.post("/api/v1/services/base")
def add_base_services(venue_id: int):
    """Вернуть локации базовые услуги, если какие-то из них удалили"""
    venue_or_404(venue_id)
    added = services_db.add_base_services(venue_id)
    return {"message": "Базовые услуги добавлены", "added": added}


# ==================== ТЕЛЕФОН ОТВЕТСТВЕННОГО (п. 14) ====================
@app.post("/api/v1/services/phone")
def set_service_phone(data: ServicePhonePackage):
    """Телефон ответственного за одну услугу"""
    if services_db.update_service_phone(data.service_id, data.contact_phone):
        return {"message": "Номер телефона обновлён"}
    raise HTTPException(status_code=404, detail="Услуга не найдена")


@app.post("/api/v1/venues/phone")
def set_venue_phone(data: VenuePhonePackage):
    """Привязка к локации номера ответственного лица: ставится всем услугам локации"""
    venue_or_404(data.venue_id)
    updated = services_db.update_venue_phone(data.venue_id, data.contact_phone)
    return {"message": "Номер телефона привязан к локации", "updated": updated}
