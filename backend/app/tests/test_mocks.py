from app.mocks import data
from app.mocks.personas import personas


def test_three_demo_accounts(client):
    items = client.get("/api/mock/citizens").json()
    assert [i["id"] for i in items] == ["P1", "P2", "P3"]
    assert items[0]["pesel_masked"].endswith("*****")


def test_login_returns_owner_and_unknown_citizen_404(client):
    ok = client.post("/api/mock/mobywatel/login", json={"citizen_id": "P3"}).json()
    assert ok["owner_id"] == "mobywatel-P3" and ok["citizen"]["first_name"] == "Joanna"
    assert client.post("/api/mock/mobywatel/login", json={"citizen_id": "S99"}).status_code == 404


def test_insurance_bases_average_matches_profile(client):
    body = client.get("/api/mock/zus/P1/insurance").json()
    assert body["insured_on_event"] is True
    assert len(body["bases"]) == 12
    assert round(sum(b["base"] for b in body["bases"]) / 12, 2) == 8200


def test_ended_insurance_is_reported():
    profile = {
        "child": {"birth_date": "2026-05-01"},
        "mother": {"employment": "employee", "insurance_ended_on": "2026-01-31"},
    }
    assert data.insurance_record(profile)["insured_on_event"] is False


def test_debt_certificate_blocks_only_above_threshold(client):
    profile = {
        "child": {"birth_date": "2026-05-01"},
        "mother": {"employment": "self_employed", "contribution_debt": 1800},
    }
    assert data.debt_certificate(profile, 48.06)["blocks_benefit"] is True
    clean = client.get("/api/mock/zus/P2/debt-certificate").json()
    assert clean["blocks_benefit"] is False


def test_ezla_for_pregnancy_sick_leave(client):
    records = client.get("/api/mock/zus/P1/ezla").json()["records"]
    assert records and records[0]["code"] == "B"
    assert client.get("/api/mock/zus/P3/ezla").json()["records"] == []


def test_zus_profile_and_pue_question(client):
    profile = client.get("/api/mock/zus/P3/profile").json()
    assert profile["father"]["employment"] == "self_employed"
    answer = client.post(
        "/api/mock/pue/question",
        json={
            "citizen_id": "P1",
            "subject": "Zadłużenie",
            "text": "Czy zaległość blokuje zasiłek?",
        },
    ).json()
    assert answer["ticket"].startswith("PUE/") and "zadłużenia" in answer["answer_pl"]


def test_every_persona_profile_is_valid_and_evaluates(client):
    for persona in personas():
        r = client.post("/api/rules/evaluate", json=persona["profile"])
        assert r.status_code == 200, (persona["id"], r.text)
        assert r.json()["payments"], persona["id"]


def test_login_with_any_valid_pesel(client):
    ok = client.post("/api/mock/mobywatel/login-pesel", json={"pesel": "44051401359", "first_name": "Ewa"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["owner_id"] == "mobywatel-pesel-44051401359"
    assert body["citizen"]["demo"] is False and body["citizen"]["first_name"] == "Ewa"
    assert client.get(f"/api/mock/zus/{body['citizen']['id']}/insurance").status_code == 404


def test_login_with_invalid_pesel_is_rejected(client):
    assert client.post("/api/mock/mobywatel/login-pesel", json={"pesel": "12345"}).status_code == 422
    assert client.post("/api/mock/mobywatel/login-pesel", json={"pesel": "44051401350"}).status_code == 422


def test_demo_pesel_opens_persona(client):
    persona = client.get("/api/mock/citizens").json()[0]
    from app.mocks.personas import CITIZENS

    r = client.post("/api/mock/mobywatel/login-pesel", json={"pesel": CITIZENS[persona["id"]]["pesel"]})
    assert r.status_code == 200 and r.json()["citizen"]["demo"] is True
