from app.core.db import SessionLocal
from app.seed import seed_parameters
from app.seed.parameters_2026 import PARAMETERS


def _by_key(response):
    return {p["key"]: p for p in response.json()["parameters"]}


def test_returns_full_2026_seed(client):
    response = client.get("/api/parameters", params={"date": "2026-11-21"})
    assert response.status_code == 200
    params = _by_key(response)
    assert set(params) == {p["key"] for p in PARAMETERS}
    assert params["maternity_leave_weeks"]["value"]["1"] == 20
    assert params["rate_averaged"]["value"] == 0.815
    assert params["minimum_wage"]["value"] == 4806.0


def test_validity_period_picks_older_version(client):
    params = _by_key(client.get("/api/parameters", params={"date": "2025-06-01"}))
    # Only the historical minimum wage existed then.
    assert params["minimum_wage"]["value"] == 4666.0
    assert "maternity_leave_weeks" not in params


def test_single_parameter_and_404(client):
    ok = client.get("/api/parameters/paternity_leave_days", params={"date": "2026-11-21"})
    assert ok.status_code == 200 and ok.json()["value"] == 14
    assert client.get("/api/parameters/does_not_exist").status_code == 404


def test_seed_is_idempotent(client):
    with SessionLocal() as db:
        assert seed_parameters(db) == 0
