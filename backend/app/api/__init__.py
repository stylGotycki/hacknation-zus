from fastapi import APIRouter

from app.api import health, parameters

# Every router is mounted under /api in main.py, so nginx can forward paths unchanged.
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(parameters.router)
