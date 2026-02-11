"""YABA. Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database import engine
from src.models import Base
from src.routers import forecasting, ingestion, production, dashboard
from src.routers import definitions, inventory, invoices


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="YABA",
    description="Kitchen management system with inventory, production, and forecasting.",
    version="0.1.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router)
app.include_router(production.router)
app.include_router(forecasting.router)
app.include_router(invoices.router)
app.include_router(inventory.router)
app.include_router(dashboard.router)
app.include_router(definitions.router)


@app.get("/")
async def root():
    return {"message": "Welcome to YABA"}
