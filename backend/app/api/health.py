from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import DbSession

router = APIRouter(tags=["system"])


@router.get("/health")
def health(db: DbSession) -> dict[str, str]:
    """Liveness check that also verifies the database connection."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
