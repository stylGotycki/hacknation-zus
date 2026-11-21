from fastapi import APIRouter
from pydantic import BaseModel

from app.rules import FamilyProfile
from app.seed.scenarios import load_scenarios

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class Scenario(BaseModel):
    id: str
    title_pl: str
    description_pl: str
    tags: list[str]
    profile: FamilyProfile


@router.get("", response_model=list[Scenario])
def list_scenarios() -> list[Scenario]:
    """Ready-made family profiles (personas) built from typical ZUS cases."""
    return [Scenario.model_validate(item) for item in load_scenarios()]
