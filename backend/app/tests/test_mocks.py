def test_citizens_one_per_scenario(client):
    items = client.get("/api/mock/citizens").json()
    assert len(items) == 12 and items[0]["pesel_masked"].endswith("*****")


def test_login_returns_owner_and_unknown_citizen_404(client):
    ok = client.post("/api/mock/mobywatel/login", json={"citizen_id": "S3"}).json()
    assert ok["owner_id"] == "mobywatel-S3" and ok["citizen"]["first_name"]
    assert client.post("/api/mock/mobywatel/login", json={"citizen_id": "S99"}).status_code == 404


def test_insurance_bases_average_matches_profile(client):
    data = client.get("/api/mock/zus/S1/insurance").json()
    assert data["insured_on_event"] is True
    assert len(data["bases"]) == 12
    assert round(sum(b["base"] for b in data["bases"]) / 12, 2) == 6000


def test_uninsured_ended_insurance_is_reported(client):
    data = client.get("/api/mock/zus/S7/insurance").json()
    assert data["insured_on_event"] is False


def test_debt_certificate_blocks_only_above_threshold(client):
    blocked = client.get("/api/mock/zus/S10/debt-certificate").json()
    assert blocked["blocks_benefit"] is True and blocked["debt_amount"] == 1800
    clean = client.get("/api/mock/zus/S1/debt-certificate").json()
    assert clean["blocks_benefit"] is False


def test_ezla_for_pregnancy_sick_leave(client):
    records = client.get("/api/mock/zus/S6/ezla").json()["records"]
    assert records and records[0]["code"] == "B"
    assert client.get("/api/mock/zus/S1/ezla").json()["records"] == []


def test_zus_profile_and_pue_question(client):
    profile = client.get("/api/mock/zus/S4/profile").json()
    assert profile["father"]["employment"] == "employee"
    answer = client.post(
        "/api/mock/pue/question",
        json={"citizen_id": "S10", "subject": "Zadłużenie", "text": "Czy zaległość blokuje zasiłek?"},
    ).json()
    assert answer["ticket"].startswith("PUE/") and "zadłużenia" in answer["answer_pl"]
