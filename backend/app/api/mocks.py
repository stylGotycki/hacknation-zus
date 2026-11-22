from datetime import UTC, date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.api.parameters import parameters_valid_on
from app.core.db import DbSession
from app.mocks import data
from app.rules import FamilyProfile
from app.seed.scenarios import load_scenarios

router = APIRouter(prefix="/mock", tags=["mocks"])
SIMULATION_NOTE = "Symulacja – dane przykładowe, nie pochodzą z ZUS."


def _scenario(citizen_id: str) -> dict:
    for scenario in load_scenarios():
        if scenario["id"] == citizen_id:
            return scenario
    raise HTTPException(404, f"Unknown citizen: {citizen_id}")


class Citizen(BaseModel):
    id: str
    first_name: str
    last_name: str
    pesel_masked: str
    scenario_title_pl: str
    scenario_description_pl: str


class LoginIn(BaseModel):
    citizen_id: str


class LoginOut(BaseModel):
    owner_id: str
    citizen: Citizen
    provider_pl: str = "mObywatel (symulacja)"


@router.get("/citizens", response_model=list[Citizen])
def citizens() -> list[dict]:
    """Personas available in the mObywatel login mock (one per scenario)."""
    return [data.citizen_card(s) for s in load_scenarios()]


@router.post("/mobywatel/login", response_model=LoginOut)
def login(
    body: LoginIn,
    db: DbSession,
    guest: Annotated[str | None, Header(alias="X-Owner-Id")] = None,
) -> dict:
    """Logs the persona in; what the guest prepared before logging in moves to the account."""
    from app.api.applications import merge_owner

    scenario = _scenario(body.citizen_id)
    owner = f"mobywatel-{body.citizen_id}"
    if guest and not guest.startswith("mobywatel-"):
        merge_owner(db, guest, owner)
    return {"owner_id": owner, "citizen": data.citizen_card(scenario)}


@router.get("/zus/{citizen_id}/insurance")
def insurance(citizen_id: str) -> dict[str, Any]:
    """Simulated download of insurance data from ZUS."""
    return {**data.insurance_record(_scenario(citizen_id)["profile"]), "note_pl": SIMULATION_NOTE}


@router.get("/zus/{citizen_id}/debt-certificate")
def debt_certificate(citizen_id: str, db: DbSession) -> dict[str, Any]:
    """Simulated certificate of contribution debt on the day the benefit right arises."""
    profile = _scenario(citizen_id)["profile"]
    on = data.event_date(profile)
    values = {p.key: p.value for p in parameters_valid_on(db, on)}
    if "minimum_wage" not in values or "contribution_debt_threshold_ratio" not in values:
        # Cases from earlier years: the law of the day is not in the seed, use today's parameters.
        values = {p.key: p.value for p in parameters_valid_on(db, date.today())}
    ratio, wage = float(values["contribution_debt_threshold_ratio"]), float(values["minimum_wage"])
    threshold = round(ratio * wage, 2)
    return {**data.debt_certificate(profile, threshold), "note_pl": SIMULATION_NOTE}


@router.get("/zus/{citizen_id}/ezla")
def ezla(citizen_id: str) -> dict[str, Any]:
    """Simulated preview of e-ZLA sick notes issued for the citizen."""
    return {
        "records": data.ezla_records(_scenario(citizen_id)["profile"]),
        "note_pl": SIMULATION_NOTE,
    }


@router.get("/zus/{citizen_id}/profile", response_model=FamilyProfile)
def zus_profile(citizen_id: str) -> FamilyProfile:
    """Data 'imported from ZUS' for the calculator: the family profile of the persona."""
    return FamilyProfile.model_validate(_scenario(citizen_id)["profile"])


class PueQuestion(BaseModel):
    citizen_id: str
    subject: str
    text: str


@router.post("/pue/question")
def pue_question(body: PueQuestion) -> dict[str, Any]:
    """Simulated question to a PUE/eZUS consultant; the answer is picked by keywords."""
    _scenario(body.citizen_id)
    now = datetime.now(UTC)
    return {
        "ticket": f"PUE/{now:%Y}/{now:%m%d%H%M%S}",
        "received_at": now.isoformat(timespec="seconds"),
        "answer_pl": data.pue_answer(f"{body.subject} {body.text}"),
        "note_pl": SIMULATION_NOTE,
    }
