from fastapi import APIRouter

from app.api import applications, health, mocks, parameters, rules, scenarios

# Every router is mounted under /api in main.py, so nginx can forward paths unchanged.
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(parameters.router)
api_router.include_router(rules.router)
api_router.include_router(scenarios.router)
api_router.include_router(applications.router)
api_router.include_router(mocks.router)
