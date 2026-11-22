from app.seed.scenarios import load_scenarios

OWNER = {"X-Owner-Id": "tester-1"}


def scenario(sid):
    return next(s for s in load_scenarios() if s["id"] == sid)["profile"]


def test_forms_are_listed():
    from app.forms import FORMS

    assert {"leave_maternity", "leave_parental", "leave_paternity", "zus_zam"} <= set(FORMS)


def test_suggestions_for_employees_are_leave_requests_to_employer(client):
    items = client.post("/api/applications/suggestions?date=2026-11-21", json=scenario("S3")).json()
    codes = {(i["form_code"], i["person"]) for i in items}
    assert ("leave_maternity", "mother") in codes
    assert ("leave_parental", "father") in codes
    assert ("leave_paternity", "father") in codes
    assert all(i["submitted_to"] == "employer" for i in items)
    maternity = next(i for i in items if i["form_code"] == "leave_maternity")
    assert (
        maternity["prefill"]["leave_start"] and maternity["prefill"]["child_date"] == "2026-05-10"
    )


def test_suggestion_for_self_employed_is_zam_to_zus(client):
    items = client.post("/api/applications/suggestions?date=2026-11-21", json=scenario("S9")).json()
    assert [i["form_code"] for i in items] == ["zus_zam"]
    assert items[0]["submitted_to"] == "zus"
    assert items[0]["prefill"]["for_maternity"] is True


def test_draft_roundtrip_and_overwrite(client):
    r = client.put(
        "/api/drafts/zus_zam", json={"step": 1, "data": {"first_name": "Ola"}}, headers=OWNER
    )
    assert r.status_code == 200
    client.put(
        "/api/drafts/zus_zam", json={"step": 2, "data": {"first_name": "Anna"}}, headers=OWNER
    )
    drafts = client.get("/api/drafts", headers=OWNER).json()
    assert len(drafts) == 1 and drafts[0]["data"]["first_name"] == "Anna" and drafts[0]["step"] == 2
    assert client.get("/api/drafts", headers={"X-Owner-Id": "other"}).json() == []


def test_submit_validates_required_and_removes_draft(client):
    client.put("/api/drafts/leave_paternity", json={"step": 0, "data": {}}, headers=OWNER)
    bad = client.post(
        "/api/applications", json={"form_code": "leave_paternity", "data": {}}, headers=OWNER
    )
    assert bad.status_code == 422
    data = {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "pesel": "90010112345",
        "employer_name": "ACME",
        "leave_start": "2026-12-01",
        "leave_end": "2026-12-14",
        "child_date": "2026-11-30",
        "declaration": True,
    }
    ok = client.post(
        "/api/applications", json={"form_code": "leave_paternity", "data": data}, headers=OWNER
    )
    assert ok.status_code == 201
    assert ok.json()["status"] == "submitted" and ok.json()["submitted_to"] == "employer"
    assert all(
        d["form_code"] != "leave_paternity" for d in client.get("/api/drafts", headers=OWNER).json()
    )


def test_application_status_advances_to_decided(client):
    apps = client.get("/api/applications", headers=OWNER).json()
    app_id = apps[0]["id"]
    assert (
        client.post(f"/api/applications/{app_id}/advance", headers=OWNER).json()["status"]
        == "in_progress"
    )
    done = client.post(f"/api/applications/{app_id}/advance", headers=OWNER).json()
    assert done["status"] == "decided" and len(done["history"]) == 3
    assert client.post(f"/api/applications/{app_id}/advance", headers=OWNER).status_code == 409
    assert (
        client.post(
            f"/api/applications/{app_id}/advance", headers={"X-Owner-Id": "other"}
        ).status_code
        == 404
    )


def test_civil_registry_extract_form_is_listed_and_submits(client):
    forms = client.get("/api/forms").json()
    definition = next(f for f in forms if f["code"] == "civil_registry_extract")
    assert definition["submitted_to"] == "registry"

    data = {
        "first_name": "Anna",
        "last_name": "Nowak",
        "pesel": "90010112345",
        "relation": "parent",
        "child_first_name": "Jan",
        "child_last_name": "Nowak",
        "child_date": "2026-05-10",
        "birth_place": "Warszawa",
        "extract_type": "short",
        "declaration": True,
    }
    r = client.post(
        "/api/applications",
        json={"form_code": "civil_registry_extract", "data": data},
        headers=OWNER,
    )
    assert r.status_code == 201, r.text
    assert r.json()["submitted_to"] == "registry"
