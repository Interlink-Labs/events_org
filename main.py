from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles

# Импортируем роутер сметы (он тоже работает без БД)
from billing.router import router as billing_router

app = FastAPI(title="Interlink-Labs API")

# Подключаем статику
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем модуль сметы
app.include_router(billing_router)

# ==================== БАЗА ДАННЫХ В ПАМЯТИ (ЗАГЛУШКИ) ====================
venues_db = {}
services_db = {}
_venue_counter = 1
_service_counter = 1

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
    global _venue_counter, _service_counter
    
    venue_id = _venue_counter
    _venue_counter += 1
    
    venues_db[venue_id] = {"id": venue_id, "name": v.name, "address": v.address, "capacity": v.capacity}
    
    # Автоматическое добавление базовых услуг (ТЗ п.13)
    base_services = [
        {"name": "Аренда зала", "desc": "Базовая аренда", "price": 10000.0},
        {"name": "Уборка", "desc": "Финальная уборка", "price": 2000.0}
    ]
    for bs in base_services:
        service_id = _service_counter
        _service_counter += 1
        services_db[service_id] = {
            "id": service_id, "venue_id": venue_id, "name": bs["name"], 
            "description": bs["desc"], "price": bs["price"], "contact_phone": "8-800-555-35-35"
        }
        
    return {"ok": True, "venue_id": venue_id, "msg": "Локация создана, базовые услуги добавлены"}

@app.get("/api/v1/venues")
def api_get_venues():
    return list(venues_db.values())

# ==================== УСЛУГИ (CRUD ДЛЯ МЕНЕДЖЕРА) ====================
@app.get("/api/v1/manager/services")
def get_all_services(venue_id: Optional[int] = None):
    if venue_id:
        return [s for s in services_db.values() if s["venue_id"] == venue_id]
    return list(services_db.values())

@app.post("/api/v1/manager/services/create")
def create_service(s: ServiceCreate):
    global _service_counter
    service_id = _service_counter
    _service_counter += 1
    
    services_db[service_id] = {
        "id": service_id, "venue_id": s.venue_id, "name": s.name,
        "description": s.description, "price": s.price, "contact_phone": s.contact_phone
    }
    return {"ok": True, "service_id": service_id}

@app.post("/api/v1/manager/services/{service_id}/update")
def update_service(service_id: int, s: ServiceUpdate):
    if service_id in services_db:
        services_db[service_id].update({
            "name": s.name, "description": s.description, 
            "price": s.price, "contact_phone": s.contact_phone
        })
        return {"ok": True, "msg": "Услуга обновлена"}
    return {"ok": False, "msg": "Услуга не найдена"}

@app.post("/api/v1/manager/services/{service_id}/delete")
def delete_service(service_id: int):
    if service_id in services_db:
        del services_db[service_id]
        return {"ok": True, "msg": "Услуга удалена"}
    return {"ok": False, "msg": "Услуга не найдена"}

# ==================== КОНТАКТЫ ====================
@app.post("/api/v1/manager/services/{service_id}/phone")
def set_contact_phone(service_id: int, p: PhoneUpdate):
    if service_id in services_db:
        services_db[service_id]["contact_phone"] = p.contact_phone
        return {"ok": True, "msg": "Номер телефона обновлен"}
    return {"ok": False, "msg": "Услуга не найдена"}

@app.get("/")
def root():
    return {"message": "API работает. Открой /docs"}
# ... (весь предыдущий код с VenueCreate, сервисами и billing)

@app.get("/")
def root():
    return {"message": "API работает. Открой /docs"}

# ==================== ЗАПУСК СЕРВЕРА ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)