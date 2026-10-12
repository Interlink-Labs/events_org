from fastapi import FastAPI
from app.api.routes import estimates, payments
from app.core.database import Base, engine

app = FastAPI(title="Interlink-Labs Events API")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # в проде — Alembic, здесь для примера
        await conn.run_sync(Base.metadata.create_all)

app.include_router(estimates.router)
app.include_router(payments.router)