#--------------МОДУЛЬ УСЛУГ--------------------#
from typing import Literal
from fastapi.security import OAuth2PasswordBearer


# ######################################################################
# ======= ДОБАВЛЕНО: АВТОРИЗАЦИЯ (JWT) — НАЧАЛО =======
# Модуль услуг НЕ проверяет токен сам, а обращается к основному
# модулю авторизации auth/security.py (get_current_user).
# Из токена берётся role: клиенту — только чтение,
# manager/admin — создание, изменение, удаление, включение/выключение.
# ######################################################################
from auth.security import get_current_user as auth_get_current_user

SERVICES_MANAGER_ROLES = {"manager", "admin"}

# Для эндпоинтов, где токен необязателен (без токена телефон скрывается)
services_optional_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def services_current_user(auth_user: dict = Depends(auth_get_current_user)) -> dict:
    """Обязательная авторизация через модуль auth: без токена -> 401."""
    return {"email": auth_user["email"], "role": str(auth_user.get("role") or "client").lower()}


def services_optional_user(token: Optional[str] = Depends(services_optional_scheme)) -> Optional[dict]:
    """Необязательная авторизация: без токена -> None, кривой токен -> 401."""
    if token is None:
        return None
    return services_current_user(auth_get_current_user(token))


def services_require_manager(user: dict = Depends(services_current_user)) -> dict:
    """Только менеджер/админ, иначе 403."""
    if user["role"] not in SERVICES_MANAGER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


def _is_services_manager(user: Optional[dict]) -> bool:
    return user is not None and user["role"] in SERVICES_MANAGER_ROLES


def _hide_service_phone(service: dict, user: Optional[dict]) -> dict:
    """Телефон ответственного лица — только авторизованным."""
    if user is None:
        service = {**service, "contact_phone": ""}
    return service
# ######################################################################
# ======= ДОБАВЛЕНО: АВТОРИЗАЦИЯ (JWT) — КОНЕЦ =======
# ######################################################################


PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{5,20}$")

def check_phone(v: str) -> str:
    v = v.strip()
    if v != services_db.DEFAULT_PHONE and not PHONE_RE.match(v):
        raise ValueError("Некорректный номер телефона")
    return v


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

class ServiceToggle(BaseModel):  # [JWT] новая схема
    # true — включить, false — выключить; не передавать — переключить на противоположное
    is_active: Optional[bool] = None

ServiceSortField = Literal["id", "name", "price", "venue_id"]  # [JWT] сортировка
ServiceSortOrder = Literal["asc", "desc"]                     # [JWT] сортировка

class ServiceUpdate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    price: float = Field(ge=0)
    contact_phone: str = services_db.DEFAULT_PHONE

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        return check_phone(v)


# [JWT] изменено: фильтр + сортировка; клиент видит только включённые, без токена телефон скрыт
@app.get("/api/v1/services", tags=["Услуги"])
def list_services(venue_id: Optional[int] = None,
                  is_base: Optional[bool] = None,
                  min_price: Optional[float] = None,
                  max_price: Optional[float] = None,
                  search: Optional[str] = None,
                  include_inactive: bool = False,
                  sort_by: Optional[ServiceSortField] = None,
                  order: ServiceSortOrder = "asc",
                  user: Optional[dict] = Depends(services_optional_user)):
    # Выключенные услуги может посмотреть только менеджер (include_inactive=true)
    only_active = not (include_inactive and _is_services_manager(user))
    services = services_db.get_services(
        venue_id=venue_id, only_active=only_active, is_base=is_base,
        min_price=min_price, max_price=max_price, search=search,
        sort_by=sort_by, order=order,
    )
    return [_hide_service_phone(s, user) for s in services]

# [JWT] изменено: выключенная услуга для клиента не существует, без токена телефон скрыт
@app.get("/api/v1/services/{service_id}", tags=["Услуги"])
def get_service(service_id: int, user: Optional[dict] = Depends(services_optional_user)):
    service = services_db.get_service(service_id)
    if service is None or (not service["is_active"] and not _is_services_manager(user)):
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return _hide_service_phone(service, user)


# ######################################################################
# ======= ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ (JWT) — НАЧАЛО =======
# Новые эндпоинты модуля «Услуги», добавленные по заданию на JWT:
#   1. PATCH /api/v1/services/{service_id}/toggle  — включить/выключить услугу, не удаляя (manager/admin)
#   2. GET   /api/v1/services/{service_id}/contact — телефон ответственного (только с токеном)
# ######################################################################

# --- 1. Включить / выключить услугу ---
@app.patch("/api/v1/services/{service_id}/toggle", tags=["Услуги"])
def toggle_service(service_id: int, payload: ServiceToggle = ServiceToggle(),
                   user: dict = Depends(services_require_manager)):
    """Выключенная услуга не удаляется, но клиенты её больше не видят."""
    new_state = services_db.set_service_active(service_id, payload.is_active)
    if new_state is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return {"message": "Услуга включена" if new_state else "Услуга выключена",
            "service": services_db.get_service(service_id)}


# --- 2. Телефон ответственного лица ---
@app.get("/api/v1/services/{service_id}/contact", tags=["Услуги"])
def get_service_contact(service_id: int, user: dict = Depends(services_current_user)):
    """Телефон ответственного за услугу (только с токеном)."""
    service = services_db.get_service(service_id)
    if service is None or (not service["is_active"] and not _is_services_manager(user)):
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return {"service_id": service["id"], "name": service["name"], "contact_phone": service["contact_phone"]}

# ######################################################################
# ======= ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ (JWT) — КОНЕЦ =======
# ######################################################################


# [JWT] изменено: только manager/admin
@app.post("/api/v1/services", status_code=status.HTTP_201_CREATED, tags=["Услуги"])
def create_service(service: ServiceCreate = ServiceCreate(),
                   user: dict = Depends(services_require_manager)):
    venue_id = get_default_venue_id()

    if service.name:
        service_id = services_db.write_service(
            venue_id, service.name, service.description,
            service.price if service.price is not None else 0.0,
            service.contact_phone,
        )
        if service_id is None:
            raise HTTPException(status_code=409, detail="Услуга с таким названием уже есть")
        return services_db.get_service(service_id)

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

# [JWT] изменено: только manager/admin
@app.put("/api/v1/services/{service_id}", tags=["Услуги"])
def update_service(service_id: int, service: ServiceUpdate,
                   user: dict = Depends(services_require_manager)):
    result = services_db.update_service(
        service_id, service.name, service.description, service.price, service.contact_phone
    )
    if result is None:
        raise HTTPException(status_code=409, detail="Услуга с таким названием уже есть")
    if not result:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return services_db.get_service(service_id)

# [JWT] изменено: только manager/admin
@app.delete("/api/v1/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Услуги"])
def delete_service(service_id: int, user: dict = Depends(services_require_manager)):
    if not services_db.delete_service(service_id):
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return None
