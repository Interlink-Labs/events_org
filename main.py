from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import services_db

app = FastAPI()

# ==================== PYDANTIC MODELS ====================
class VenueCreate(BaseModel):
    name: str
    address: str
    capacity: int

class ServiceCreate(BaseModel):
    venue_id: int
    name: str
    description: Optional[str] = None
    price: float = 0.0
    contact_phone: Optional[str] = "Не указан"

class ServiceUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    contact_phone: str

class PhoneUpdate(BaseModel):
    contact_phone: str

# ==================== ЛОКАЦИИ ====================
@app.post("/api/v1/venues/create")
def api_create_venue(v: VenueCreate):
    """Создает локацию и автоматически добавляет базовые услуги"""
    venue_id = services_db.create_venue(v.name, v.address, v.capacity)
    return {"ok": True, "venue_id": venue_id, "msg": "Локация создана, базовые услуги добавлены"}

@app.get("/api/v1/venues")
def api_get_venues():
    return services_db.get_venues()

# ==================== УСЛУГИ (CRUD ДЛЯ МЕНЕДЖЕРА) ====================

@app.get("/api/v1/manager/services")
def get_all_services(venue_id: Optional[int] = None):
    """Получить все услуги или услуги конкретной локации"""
    return services_db.get_services(venue_id)

@app.post("/api/v1/manager/services/create")
def create_service(s: ServiceCreate):
    if not services_db.get_venues(): # Просто проверка, что БД жива
        pass
    service_id = services_db.create_service(
        s.venue_id, s.name, s.description, s.price, s.contact_phone
    )
    return {"ok": True, "service_id": service_id}

@app.post("/api/v1/manager/services/{service_id}/update")
def update_service(service_id: int, s: ServiceUpdate):
    if services_db.update_service(service_id, s.name, s.description, s.price, s.contact_phone):
        return {"ok": True, "msg": "Услуга обновлена"}
    return {"ok": False, "msg": "Услуга не найдена"}

@app.post("/api/v1/manager/services/{service_id}/delete")
def delete_service(service_id: int):
    if services_db.delete_service(service_id):
        return {"ok": True, "msg": "Услуга удалена"}
    return {"ok": False, "msg": "Услуга не найдена"}

# ==================== КОНТАКТЫ ====================
@app.post("/api/v1/manager/services/{service_id}/phone")
def set_contact_phone(service_id: int, p: PhoneUpdate):
    """14) Привязка к локации контактного номера телефона ответственного"""
    if services_db.update_contact_phone(service_id, p.contact_phone):
        return {"ok": True, "msg": "Номер телефона обновлен"}
    return {"ok": False, "msg": "Услуга не найдена"}
