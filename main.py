import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from clients.router import client_bp
from billing.router import router as billing_router
from auth.router import router as auth_router
from events.router import router as events_router


app = FastAPI(title="Interlink-Labs Events API")

# статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")

# подключаем роутеры
app.include_router(client_bp)              # /api/v1/client/...
app.include_router(auth_router)            # /api/v1/auth/...
app.include_router(events_router)          # /api/v1/events/...
app.include_router(billing_router)         # /api/v1/billing/...


@app.get("/")
def root():
    return {"message": "API работает. Открой /docs"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)