from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import engine, get_db, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interlink-Labs API")
app.mount("/static", StaticFiles(directory="static"), name="static")

from billing.router import router as billing_router
app.include_router(billing_router)

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

@app.post("/api/v1/venues/create")
def api_create_venue(v: VenueCreate, db: Session = Depends(get_db)):
    venue = models.Venue(name=v.name, address=v.address, capacity=v.capacity)
    db.add(venue)
    db.commit()
    db.refresh(venue)
    
    base_services = [
        models.Service(venue_id=venue.id, name="Аренда зала", description="Базовая аренда", price=10000.0),
        models.Service(venue_id=venue.id, name="Уборка", description="Финальная уборка", price=2000.0)
    ]
    db.add_all(base_services)
    db.commit()
    return {"ok": True, "venue_id": venue.id, "msg": "Локация создана"}

@app.get("/api/v1/venues")
def api_get_venues(db: Session = Depends(get_db)):
    return db.query(models.Venue).all()

@app.get("/api/v1/manager/services")
def get_all_services(venue_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Service)
    if venue_id:
        query = query.filter(models.Service.venue_id == venue_id)
    return query.all()

@app.post("/api/v1/manager/services/create")
def create_service(s: ServiceCreate, db: Session = Depends(get_db)):
    service = models.Service(venue_id=s.venue_id, name=s.name, description=s.description, price=s.price, contact_phone=s.contact_phone)
    db.add(service)
    db.commit()
    db.refresh(service)
    return {"ok": True, "service_id": service.id}

@app.post("/api/v1/manager/services/{service_id}/update")
def update_service(service_id: int, s: ServiceUpdate, db: Session = Depends(get_db)):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(404, "Услуга не найдена")
    service.name = s.name
    service.description = s.description
    service.price = s.price
    service.contact_phone = s.contact_phone
    db.commit()
    return {"ok": True, "msg": "Услуга обновлена"}

@app.post("/api/v1/manager/services/{service_id}/delete")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(404, "Услуга не найдена")
    db.delete(service)
    db.commit()
    return {"ok": True, "msg": "Услуга удалена"}

@app.post("/api/v1/manager/services/{service_id}/phone")
def set_contact_phone(service_id: int, p: PhoneUpdate, db: Session = Depends(get_db)):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if service:
        service.contact_phone = p.contact_phone
        db.commit()
        return {"ok": True, "msg": "Номер обновлен"}
    return {"ok": False, "msg": "Услуга не найдена"}

@app.get("/")
def root():
    return {"message": "API работает. Открой /docs"}