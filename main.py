from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# ИМПОРТЫ МОДУЛЕЙ
# ==========================================
# Мы импортируем приложения или роутеры из папок модулей.
# Если модуль еще не готов (или упал), сервер все равно запустится.

try:
    from clients.main import app as clients_app
except ImportError:
    logger.warning("⚠️ Модуль 'clients' не найден или не содержит 'app'")
    clients_app = None

try:
    from modiule_events.main import app as events_app
except ImportError:
    logger.warning("⚠️ Модуль 'modiule_events' не найден или не содержит 'app'")
    events_app = None

try:
    from module_Estimate.main import app as estimate_app
except ImportError:
    logger.warning("⚠️ Модуль 'module_Estimate' не найден или не содержит 'app'")
    estimate_app = None

try:
    from module_services.main import app as services_app
except ImportError:
    logger.warning("⚠️ Модуль 'module_services' не найден или не содержит 'app'")
    services_app = None


# ==========================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск главного приложения...")
    yield
    logger.info("🛑 Остановка приложения...")


main_app = FastAPI(
    title="Главный API Проекта",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# МОНТИРОВАНИЕ МОДУЛЕЙ
# ==========================================
# Каждому модулю выделяется свой префикс (URL).
# Например: /api/clients/..., /api/events/...

if clients_app:
    main_app.mount("/api/clients", clients_app)
    logger.info("✅ Подключен модуль: clients")

if events_app:
    main_app.mount("/api/events", events_app)
    logger.info("✅ Подключен модуль: modiule_events")

if estimate_app:
    main_app.mount("/api/estimate", estimate_app)
    logger.info("✅ Подключен модуль: module_Estimate")

if services_app:
    main_app.mount("/api/services", services_app)
    logger.info("✅ Подключен модуль: module_services")


# ==========================================
# БАЗОВЫЙ ЭНДПОИНТ
# ==========================================

@main_app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности главного сервиса."""
    return {
        "status": "ok",
        "modules_loaded": {
            "clients": clients_app is not None,
            "events": events_app is not None,
            "estimate": estimate_app is not None,
            "services": services_app is not None,
        }
    }

# Для запуска через uvicorn app.main:app, если нужно
app = main_app
print("Модуль 42 сработал успешно")
