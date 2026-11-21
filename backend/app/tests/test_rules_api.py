from datetime import date


def _payload(**overrides):
    body = {
        "child": {"birth_date": "2026-11-10"},
        "mother": {
            "employment": "employee",
            "average_monthly_base": 6000,
            "employer_insured_count": 50,
        },
    }
    body.update(overrides)
    return body


def test_evaluate_endpoint_returns_full_result(client):
    response = client.post("/api/rules/evaluate", params={"date": "2026-11-21"}, json=_payload())
    assert response.status_code == 200
    data = response.json()
    assert data["params_date"] == "2026-11-21"
    codes = {b["code"] for b in data["benefits"]}
    assert {"maternity_allowance_mother", "parental_allowance_mother"} <= codes
    assert data["timeline"][0]["kind"] == "maternity"
    assert data["totals"]["family_gross"] > 0


def test_evaluate_defaults_to_today(client):
    response = client.post("/api/rules/evaluate", json=_payload())
    assert response.status_code == 200
    assert response.json()["params_date"] == date.today().isoformat()


def test_evaluate_rejects_invalid_plan_with_422(client):
    body = _payload(plan={"maternity_before_birth_weeks": 9})
    response = client.post("/api/rules/evaluate", params={"date": "2026-11-21"}, json=body)
    assert response.status_code == 422
    assert "6 weeks" in response.json()["detail"]


def test_evaluate_rejects_profile_without_parent_or_date(client):
    no_parent = client.post("/api/rules/evaluate", json={"child": {"birth_date": "2026-11-10"}})
    assert no_parent.status_code == 422
    no_date = client.post(
        "/api/rules/evaluate", json={"child": {}, "mother": {"employment": "employee"}}
    )
    assert no_date.status_code == 422


def test_evaluate_uses_parameters_valid_on_the_given_date(client):
    # In mid-2025 only the historical minimum wage exists, so the engine reports it clearly.
    response = client.post("/api/rules/evaluate", params={"date": "2025-06-01"}, json=_payload())
    assert response.status_code == 409
    assert "not valid on 2025-06-01" in response.json()["detail"]


def test_openapi_documents_rules_endpoint(client):
    schema = client.get("/api/openapi.json").json()
    assert "/api/rules/evaluate" in schema["paths"]
