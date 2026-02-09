"""YABA - Yet Another Back-of-house App. Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database import engine
from src.models import Base
from src.routers import forecasting, ingestion, production


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="YABA - Yet Another Back-of-house App",
    description="Kitchen management system with inventory, production, and forecasting.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingestion.router)
app.include_router(production.router)
app.include_router(forecasting.router)


@app.get("/")
async def root():
    return {"message": "Welcome to YABA - Yet Another Back-of-house App"}
