from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.core.config import get_settings
from app.core.db import SessionLocal, init_db
from app.seed import seed_parameters

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # On every start: make sure tables exist and legal parameters are up to date.
    init_db()
    if settings.seed_on_startup:
        with SessionLocal() as db:
            seed_parameters(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    # Docs live under /api so they work through the same nginx route as the API.
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.include_router(api_router, prefix="/api")
