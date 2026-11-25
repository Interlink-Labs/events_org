# ==================== УСЛУГИ (модуль services) ====================
# Работает так же, как /venues в модуле мероприятий:
#   GET    /api/v1/services          — все услуги
#   GET    /api/v1/services/{id}     — одна услуга
#   POST   /api/v1/services          — создать (можно с пустым body)
#   PUT    /api/v1/services/{id}     — изменить
#   DELETE /api/v1/services/{id}     — удалить

PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{5,20}$")

def check_phone(v: str) -> str:
    v = v.strip()
    if v != services_db.DEFAULT_PHONE and not PHONE_RE.match(v):
        raise ValueError("Некорректный номер телефона")
    return v

# Готовые услуги: если в body нет name, берётся первая, которой ещё нет
PRESET_SERVICES = [
    ("Кейтеринг", "Фуршет или банкет под ключ", 1500.0),
    ("Звуковое оборудование", "Колонки, микрофоны, пульт", 8000.0),
    ("Световое оформление", "Сценический свет и подсветка зала", 6000.0),
    ("Фотограф", "Съёмка мероприятия, 3 часа", 10000.0),
    ("Видеосъёмка", "Съёмка и монтаж ролика", 15000.0),
    ("Ведущий", "Ведущий / тамада на мероприятие", 12000.0),
    ("DJ", "Музыкальное сопровождение", 9000.0),
    ("Декор зала", "Шары, цветы, тематическое оформление", 7000.0),
    ("Проектор и экран", "Для презентаций и видео", 3000.0),
    ("Охрана", "Охранник на время мероприятия", 4000.0),
    ("Гардероб", "Гардеробщик на входе", 2000.0),
    ("Уборка после мероприятия", "Клининг зала", 3500.0),
]

# В базе услуга обязательно привязана к локации (так устроен services_db).
# Чтобы пользователю не думать о локациях, услуги вешаются на одну
# служебную локацию, которая создаётся автоматически.
_default_venue_id: Optional[int] = None

def get_default_venue_id() -> int:
    global _default_venue_id
    if _default_venue_id is not None and services_db.check_venue(_default_venue_id):
        return _default_venue_id
    if services_db.check_venue(1):
        _default_venue_id = 1
    else:
        _default_venue_id = services_db.write_venue("Общие услуги", "—", 1)
    return _default_venue_id


class ServiceCreate(BaseModel):
    # всё необязательное — можно слать пустой body
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    contact_phone: str = services_db.DEFAULT_PHONE

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        return check_phone(v)

class ServiceUpdate(BaseModel):
    # при изменении поля обязательны — пустой PUT не затрёт услугу
    name: str = Field(min_length=1)
    description: Optional[str] = None
    price: float = Field(ge=0)
    contact_phone: str = services_db.DEFAULT_PHONE

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        return check_phone(v)


@app.get("/api/v1/services", tags=["Услуги"])
def list_services():
    return services_db.get_services(None)

@app.get("/api/v1/services/{service_id}", tags=["Услуги"])
def get_service(service_id: int):
    service = services_db.get_service(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return service

@app.post("/api/v1/services", status_code=status.HTTP_201_CREATED, tags=["Услуги"])
def create_service(service: ServiceCreate = ServiceCreate()):
    venue_id = get_default_venue_id()

    # name указан — создаём именно эту услугу
    if service.name:
        service_id = services_db.write_service(
            venue_id, service.name, service.description,
            service.price if service.price is not None else 0.0,
            service.contact_phone,
        )
        if service_id is None:
            raise HTTPException(status_code=409, detail="Услуга с таким названием уже есть")
        return services_db.get_service(service_id)

    # name не указан — берём первую готовую услугу, которой ещё нет
    for name, description, price in PRESET_SERVICES:
        service_id = services_db.write_service(
            venue_id, name,
            service.description if service.description is not None else description,
            service.price if service.price is not None else price,
            service.contact_phone,
        )
        if service_id is not None:
            return services_db.get_service(service_id)

    raise HTTPException(status_code=409, detail="Все готовые услуги уже созданы, укажи name")

@app.put("/api/v1/services/{service_id}", tags=["Услуги"])
def update_service(service_id: int, service: ServiceUpdate):
    result = services_db.update_service(
        service_id, service.name, service.description, service.price, service.contact_phone
    )
    if result is None:
        raise HTTPException(status_code=409, detail="Услуга с таким названием уже есть")
    if not result:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return services_db.get_service(service_id)

@app.delete("/api/v1/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Услуги"])
def delete_service(service_id: int):
    if not services_db.delete_service(service_id):
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return None
