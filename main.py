import traceback
from fastapi import FastAPI, HTTPException, Response, Cookie, status, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from auth.security import create_access_token as t
from fast_jwt import FastJWT
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
        
#        if cllients.write_user(username, password):
#           access_token = fast_jwt.create_access_token(
#                user_id=username, expires_delta=timedelta(minutes=30)
#            )
#            refresh_token = fast_jwt.create_refresh_token(
#                user_id=username, expires_delta=timedelta(minutes=30)
#            )
#
#            response.set_cookie(
#                key="refresh_token",
#                value=refresh_token,
#                httponly=True,   # Важно для безопасности
#                secure=True,     # Только для HTTPS
#                samesite="lax"   # или "strict"
#            )
#            return {"access_token": access_token}
#
#        else:
#            return 'юзернейм занят'

        return t({"sub": username, "role": "admin"})
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
def get_client(username: str, auth_user: dict = Depends(auth_get_current_user)):
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

@app.get("/api/v1/clients/get_by_half")
def get_clients(half_username: str):
    cllients.get_users_by_half(half_username)

# ==================== МОДУЛЬ МЕРОПРИЯТИЙ ====================
from typing import Literal, Union
from fastapi.security import OAuth2PasswordBearer


# ######################################################################
# ======= ДОБАВЛЕНО: АВТОРИЗАЦИЯ (JWT) — НАЧАЛО =======
# Модуль мероприятий НЕ проверяет токен сам, а обращается к основному
# модулю авторизации auth/security.py (get_current_user).
# Из токена берутся: sub (email пользователя) и role.
# ######################################################################
from auth.security import get_current_user as auth_get_current_user

MANAGER_ROLES = {"manager", "admin"}

# Тот же адрес выдачи токена, что и в auth/security.py, но без автоошибки —
# нужно для эндпоинтов, где токен необязателен (телефон локации скрывается)
events_optional_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class CurrentUser(BaseModel):
    id: str            # sub из токена (email)
    role: str = "client"

    @property
    def is_manager(self) -> bool:
        return self.role in MANAGER_ROLES


def _to_current_user(auth_user: dict) -> CurrentUser:
    return CurrentUser(id=str(auth_user["email"]),
                       role=str(auth_user.get("role") or "client").lower())


def events_current_user(auth_user: dict = Depends(auth_get_current_user)) -> CurrentUser:
    """Обязательная авторизация через модуль auth: без токена -> 401."""
    return _to_current_user(auth_user)


def events_optional_user(token: Optional[str] = Depends(events_optional_scheme)) -> Optional[CurrentUser]:
    """Необязательная авторизация: без токена -> None, кривой токен -> 401."""
    if token is None:
        return None
    return _to_current_user(auth_get_current_user(token))


def events_require_manager(user: CurrentUser = Depends(events_current_user)) -> CurrentUser:
    """Только менеджер/админ, иначе 403."""
    if not user.is_manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


def _get_event_checked(event_id: int, user: CurrentUser) -> dict:
    """Мероприятие + проверка владельца: клиент видит только свои, менеджер — все."""
    event = events_db.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if not user.is_manager and str(event["client_id"]) != user.id:
        raise HTTPException(status_code=403, detail="Это не ваше мероприятие")
    return event


def _hide_phone(venue: dict, user: Optional[CurrentUser]) -> dict:
    """Телефон ответственного лица — только авторизованным."""
    if user is None:
        venue = {**venue, "contact_phone": ""}
    return venue


def _sort_venues(venues: list, sort_by: str, order: str) -> list:
    return sorted(venues, key=lambda v: v[sort_by], reverse=(order == "desc"))
# ######################################################################
# ======= ДОБАВЛЕНО: АВТОРИЗАЦИЯ (JWT) — КОНЕЦ =======
# ######################################################################


# ==================== СХЕМЫ ====================
SortOrder = Literal["asc", "desc"]                                                        # [JWT] сортировка
EventSortField = Literal["id", "date", "created_at", "participants", "total_amount", "status"]  # [JWT] сортировка
VenueSortField = Literal["id", "name", "capacity"]                                        # [JWT] сортировка

class VenueBase(BaseModel):
    name: str
    address: str
    capacity: int = Field(gt=0)
    description: Optional[str] = ""
    contact_phone: Optional[str] = ""

class VenueCreate(VenueBase):
    # значения по умолчанию — можно слать POST /venues с пустым body
    name: str = "Новая локация"
    address: str = "Адрес не указан"
    capacity: int = Field(default=10, gt=0)

class VenueResponse(VenueBase):
    id: int

class VenueContactResponse(BaseModel):  # [JWT] новая схема
    venue_id: int
    name: str
    contact_phone: str

class BusySlot(BaseModel):  # [JWT] новая схема
    event_id: int
    time_start: str
    time_end: str
    status: str

class VenueAvailabilityResponse(BaseModel):  # [JWT] новая схема
    venue_id: int
    date: date
    capacity: int
    is_free: Optional[bool] = None   # заполняется, если переданы time_start и time_end
    busy_slots: List[BusySlot]

class EventBase(BaseModel):
    client_id: Union[int, str]   # [JWT] изменено: теперь тут email из токена
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

class EventCreate(EventBase):  # [JWT] изменено
    # Клиенту client_id не нужен — берётся из токена.
    # Менеджер может указать client_id, чтобы оформить заявку за клиента.
    client_id: Optional[Union[int, str]] = None

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

VALID_STATUSES = {"pending", "approved", "rejected", "completed", "cancelled"}  # [JWT] добавлен cancelled


# ==================== ЛОКАЦИИ ====================
# [JWT] изменено: без токена телефон скрыт + сортировка
@app.get("/api/v1/venues", response_model=List[VenueResponse], tags=["Мероприятия"])
def list_events_venues(sort_by: VenueSortField = "id", order: SortOrder = "asc",
                       user: Optional[CurrentUser] = Depends(events_optional_user)):
    venues = _sort_venues(events_db.get_all_venues(), sort_by, order)
    return [_hide_phone(v, user) for v in venues]

# [JWT] изменено: без токена телефон скрыт + сортировка
@app.get("/api/v1/venues/free", response_model=List[VenueResponse], tags=["Мероприятия"])
def list_free_venues(date_str: date, participants: int = 1,
                     sort_by: VenueSortField = "capacity", order: SortOrder = "asc",
                     user: Optional[CurrentUser] = Depends(events_optional_user)):
    venues = _sort_venues(events_db.get_free_venues(str(date_str), participants), sort_by, order)
    return [_hide_phone(v, user) for v in venues]

# [JWT] изменено: без токена телефон скрыт
@app.get("/api/v1/venues/{venue_id}", response_model=VenueResponse, tags=["Мероприятия"])
def get_events_venue(venue_id: int, user: Optional[CurrentUser] = Depends(events_optional_user)):
    v = events_db.get_venue(venue_id)
    if not v:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    return _hide_phone(v, user)

# [JWT] изменено: только manager/admin
@app.post("/api/v1/venues", response_model=VenueResponse, status_code=status.HTTP_201_CREATED, tags=["Мероприятия"])
def create_events_venue(venue: VenueCreate = VenueCreate(),
                        user: CurrentUser = Depends(events_require_manager)):
    new_id = events_db.create_venue(venue.name, venue.address, venue.capacity, venue.description, venue.contact_phone)
    return events_db.get_venue(new_id)

# [JWT] изменено: только manager/admin
@app.put("/api/v1/venues/{venue_id}", response_model=VenueResponse, tags=["Мероприятия"])
def update_events_venue(venue_id: int, venue: VenueBase,
                        user: CurrentUser = Depends(events_require_manager)):
    # VenueBase без значений по умолчанию — пустой PUT не затрёт локацию
    if not events_db.get_venue(venue_id):
        raise HTTPException(status_code=404, detail="Локация не найдена")
    ok = events_db.update_venue(venue_id, venue.name, venue.address, venue.capacity, venue.description, venue.contact_phone)
    if not ok:
        raise HTTPException(status_code=400, detail="Не удалось обновить локацию")
    return events_db.get_venue(venue_id)

# [JWT] изменено: только manager/admin
@app.delete("/api/v1/venues/{venue_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Мероприятия"])
def delete_events_venue(venue_id: int, user: CurrentUser = Depends(events_require_manager)):
    if not events_db.get_venue(venue_id):
        raise HTTPException(status_code=404, detail="Локация не найдена")
    if not events_db.delete_venue(venue_id):
        raise HTTPException(status_code=400, detail="Нельзя удалить локацию, по которой есть активные брони")
    return None


# ==================== МЕРОПРИЯТИЯ ====================
# [JWT] изменено: client_id берётся из токена
@app.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED, tags=["Мероприятия"])
def create_event(event: EventCreate, user: CurrentUser = Depends(events_current_user)):
    # Клиент всегда создаёт заявку на себя, даже если прислал чужой client_id
    client_id = event.client_id if (user.is_manager and event.client_id) else user.id
    ok, result = events_db.create_event(
        client_id=client_id, location_id=event.location_id, event_type=event.event_type,
        date_str=str(event.date), time_start=event.time_start, time_end=event.time_end,
        participants=event.participants, total_amount=event.total_amount, comment=event.comment,
        services=event.services, service_configs=event.service_configs,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=result)
    return events_db.get_event(result)

# [JWT] изменено: клиент видит только свои мероприятия + сортировка
@app.get("/events", response_model=List[EventResponse], tags=["Мероприятия"])
def list_events(client_id: Optional[str] = None, status_filter: Optional[str] = None,
                sort_by: EventSortField = "id", order: SortOrder = "asc",
                user: CurrentUser = Depends(events_current_user)):
    # Клиент видит только свои мероприятия, менеджер — все (с фильтром по client_id)
    if not user.is_manager:
        client_id = user.id
    return events_db.get_events(client_id, status_filter, sort_by, order)


# ######################################################################
# ======= ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ (JWT) — НАЧАЛО =======
# Новые эндпоинты модуля «Мероприятия», добавленные по заданию на JWT:
#   1. GET  /events/my                            — мероприятия текущего пользователя
#   2. POST /events/{event_id}/cancel             — отмена своего мероприятия + снятие брони
#   3. GET  /api/v1/venues/{venue_id}/availability — свободна ли площадка на дату/время
#   4. GET  /api/v1/venues/{venue_id}/contact      — телефон ответственного (только с токеном)
# Блок стоит ДО GET /events/{event_id}, иначе /events/my не сработает.
# ######################################################################

# --- 1. Мероприятия текущего пользователя ---
@app.get("/events/my", response_model=List[EventResponse], tags=["Мероприятия"])
def list_my_events(status_filter: Optional[str] = None,
                   sort_by: EventSortField = "date", order: SortOrder = "asc",
                   user: CurrentUser = Depends(events_current_user)):
    """Мероприятия текущего пользователя (берётся из токена)."""
    return events_db.get_events(user.id, status_filter, sort_by, order)


# --- 2. Отмена своего мероприятия ---
@app.post("/events/{event_id}/cancel", response_model=EventResponse, tags=["Мероприятия"])
def cancel_event(event_id: int, user: CurrentUser = Depends(events_current_user)):
    """Отмена своего мероприятия. Бронь площадки снимается автоматически."""
    _get_event_checked(event_id, user)
    ok, err = events_db.cancel_event(event_id)
    if not ok:
        raise HTTPException(status_code=400, detail=err)
    return events_db.get_event(event_id)


# --- 3. Проверка свободности площадки ---
@app.get("/api/v1/venues/{venue_id}/availability", response_model=VenueAvailabilityResponse, tags=["Мероприятия"])
def get_venue_availability(venue_id: int, date_str: date,
                           time_start: Optional[str] = None, time_end: Optional[str] = None,
                           user: CurrentUser = Depends(events_current_user)):
    """
    Свободна ли площадка на дату. Без времени — список занятых интервалов.
    С time_start и time_end — ещё и is_free для конкретного интервала.
    """
    v = events_db.get_venue(venue_id)
    if not v:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    if (time_start is None) != (time_end is None):
        raise HTTPException(status_code=400, detail="Укажите и time_start, и time_end")

    is_free = None
    if time_start is not None:
        try:
            is_free = events_db.is_venue_free(venue_id, str(date_str), time_start, time_end)
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="Время должно быть в формате HH:MM")

    return {
        "venue_id": venue_id,
        "date": date_str,
        "capacity": v["capacity"],
        "is_free": is_free,
        "busy_slots": events_db.get_busy_slots(venue_id, str(date_str)),
    }


# --- 4. Контакт ответственного лица ---
@app.get("/api/v1/venues/{venue_id}/contact", response_model=VenueContactResponse, tags=["Мероприятия"])
def get_venue_contact(venue_id: int, user: CurrentUser = Depends(events_current_user)):
    """Телефон ответственного лица за локацию (только с токеном)."""
    v = events_db.get_venue(venue_id)
    if not v:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    return {"venue_id": v["id"], "name": v["name"], "contact_phone": v["contact_phone"]}

# ######################################################################
# ======= ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ (JWT) — КОНЕЦ =======
# ######################################################################


# [JWT] изменено: проверка владельца
@app.get("/events/{event_id}", response_model=EventResponse, tags=["Мероприятия"])
def get_event(event_id: int, user: CurrentUser = Depends(events_current_user)):
    return _get_event_checked(event_id, user)

# [JWT] изменено: проверка владельца + перепроверка брони
@app.put("/events/{event_id}", response_model=EventResponse, tags=["Мероприятия"])
def update_event(event_id: int, payload: EventUpdate, user: CurrentUser = Depends(events_current_user)):
    event = _get_event_checked(event_id, user)
    if not user.is_manager and event["status"] != "pending":
        raise HTTPException(status_code=400, detail="Изменить можно только заявку в статусе pending")

    data = payload.model_dump(exclude_unset=True)
    if "date" in data:
        data["date"] = str(data["date"])

    # Если меняются дата/время/участники — заново проверяем бронь (без учёта самой заявки)
    if {"date", "time_start", "time_end", "participants"} & data.keys() \
            and event["status"] in events_db.ACTIVE_STATUSES:
        ok, err = events_db.check_event_slot(
            event["location_id"],
            data.get("date", event["date"]),
            data.get("time_start", event["time_start"]),
            data.get("time_end", event["time_end"]),
            data.get("participants", event["participants"]),
            exclude_event_id=event_id,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=err)

    if not events_db.update_event(event_id, data):
        raise HTTPException(status_code=400, detail="Не удалось обновить мероприятие")
    return events_db.get_event(event_id)

# [JWT] изменено: только manager/admin + перепроверка брони
@app.put("/events/{event_id}/status", tags=["Мероприятия"])
def update_event_status(event_id: int, payload: StatusUpdate,
                        user: CurrentUser = Depends(events_require_manager)):
    if payload.new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Допустимые статусы: {sorted(VALID_STATUSES)}")
    event = events_db.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    # Возврат в активный статус (например, из cancelled) — площадка могла уже уйти
    if payload.new_status in events_db.ACTIVE_STATUSES and event["status"] not in events_db.ACTIVE_STATUSES:
        ok, err = events_db.check_event_slot(
            event["location_id"], event["date"], event["time_start"], event["time_end"],
            event["participants"], exclude_event_id=event_id,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=err)

    events_db.update_event_status(event_id, payload.new_status)
    return {"message": "Статус обновлён", "event_id": event_id, "status": payload.new_status}

# [JWT] изменено: только manager/admin
@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Мероприятия"])
def delete_event(event_id: int, user: CurrentUser = Depends(events_require_manager)):
    # Клиент своё мероприятие не удаляет, а отменяет через /events/{id}/cancel
    if not events_db.delete_event(event_id):
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return None

@app.get("/")
def root():
    return {"message": "API работает. Открой /docs"}
