from app.seed.scenarios import load_scenarios

OWNER = {"X-Owner-Id": "tester-1"}


def scenario(sid):
    return next(s for s in load_scenarios() if s["id"] == sid)["profile"]


def test_forms_follow_the_regulations():
    """Every leave request cites its RW paragraph; ZAM cites załącznik nr 6 RZ."""
    from app.forms import FORMS

    expected = {
        "leave_maternity_before": "§ 2 RW",
        "leave_maternity_resignation": "§ 3 RW",
        "leave_maternity_father": "§ 5 RW",
        "leave_supplementary": "§ 14 RW",
        "leave_parental": "§ 15 RW",
        "parental_work": "§ 16 RW",
        "leave_paternity": "§ 17 RW",
        "leave_taken_in": "§ 18 RW",
        "zus_zam": "załącznik nr 6 RZ",
    }
    for code, basis in expected.items():
        assert basis in FORMS[code].legal_basis_pl, code
        assert FORMS[code].body, code
    # RW § 15 ust. 2 pkt 2: the statement about the other parent is part of the request.
    keys = {f.key for s in FORMS["leave_parental"].steps for f in s.fields}
    assert {"used_so_far", "used_parts", "other_parent"} <= keys
    # Załącznik 6 pkt 17: bank account; pkt 15: full leave (81,5%).
    keys = {f.key for s in FORMS["zus_zam"].steps for f in s.fields}
    assert {"bank_account", "full_leave", "payer_name", "pesel", "za_zyciem"} <= keys


def test_conditional_fields_are_required_only_when_shown():
    from app.forms import FORMS, missing_fields

    form = FORMS["leave_parental"]
    base = {
        "first_name": "A",
        "last_name": "B",
        "employer_name": "C",
        "place": "D",
        "applicant_role": "mother",
        "situation": "birth",
        "leave_start": "2026-12-01",
        "leave_end": "2027-01-01",
        "used_so_far": "nie",
        "used_parts": 0,
        "other_parent": "none",
        "declaration": True,
    }
    assert missing_fields(form, base) == []
    assert missing_fields(form, {**base, "other_parent": "period"}) == ["other_parent_period"]
    assert "placement_date" in missing_fields(form, {**base, "situation": "adoption"})
    assert missing_fields(form, {**base, "declaration": False}) == ["declaration"]


def test_suggestions_for_employees_are_leave_requests_to_employer(client):
    items = client.post("/api/applications/suggestions?date=2026-11-21", json=scenario("S3")).json()
    codes = {(i["form_code"], i["person"]) for i in items}
    assert ("leave_parental", "mother") in codes
    assert ("leave_parental", "father") in codes
    assert ("leave_paternity", "father") in codes
    assert all(i["submitted_to"] == "employer" for i in items)
    paternity = next(i for i in items if i["form_code"] == "leave_paternity")
    assert paternity["deadline_codes"] == ["t_ojcowski"] and paternity["prefill"]["leave_start"]
    parental = next(
        i for i in items if i["form_code"] == "leave_parental" and i["person"] == "father"
    )
    assert parental["prefill"]["applicant_role"] == "father"


def test_overdue_suggestion_carries_advice(client):
    items = client.post("/api/applications/suggestions?on=2026-11-21", json=scenario("S3")).json()
    overdue = [i for i in items if i["status"] == "overdue"]
    assert overdue and all(i["late_pl"] for i in overdue)


def test_suggestion_prefills_identity_of_logged_in_citizen(client):
    items = client.post(
        "/api/applications/suggestions", json=scenario("S3"), headers={"X-Owner-Id": "mobywatel-S3"}
    ).json()
    mother = next(i for i in items if i["person"] == "mother")
    father = next(i for i in items if i["person"] == "father")
    assert mother["prefill"]["first_name"] == "Marta" and "first_name" not in father["prefill"]


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
        "employer_name": "ACME",
        "place": "Warszawa",
        "leave_start": "2026-12-01",
        "leave_end": "2026-12-14",
        "used_before": "no",
        "declaration": True,
    }
    ok = client.post(
        "/api/applications", json={"form_code": "leave_paternity", "data": data}, headers=OWNER
    )
    assert ok.status_code == 201
    assert ok.json()["status"] == "submitted" and ok.json()["submitted_to"] == "employer"
    assert ok.json()["person"] == "father" and ok.json()["fulfils"] == ["t_ojcowski"]
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
        "applicant_role": "mother",
        "place": "Warszawa",
        "child_first_name": "Jan",
        "child_last_name": "Nowak",
        "child_birth_date": "2026-05-10",
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


def test_role_drafts_are_separate(client):
    owner = {"X-Owner-Id": "tester-roles"}
    client.put(
        "/api/drafts/leave_parental:mother",
        json={"step": 1, "data": {"first_name": "A"}},
        headers=owner,
    )
    client.put(
        "/api/drafts/leave_parental:father",
        json={"step": 2, "data": {"first_name": "B"}},
        headers=owner,
    )
    drafts = client.get("/api/drafts", headers=owner).json()
    assert {d["form_code"] for d in drafts} == {"leave_parental:mother", "leave_parental:father"}


def test_state_is_saved_per_owner_and_merged_on_login(client):
    guest = {"X-Owner-Id": "guest-xyz"}
    state = {"form": {"stage": "born"}, "step": 3, "profile": {"child": {}}}
    assert client.put("/api/state", json=state, headers=guest).json()["step"] == 3
    client.put(
        "/api/drafts/zus_zam", json={"step": 1, "data": {"first_name": "Gość"}}, headers=guest
    )
    assert client.get("/api/state", headers={"X-Owner-Id": "someone"}).json()["form"] is None

    r = client.post("/api/mock/mobywatel/login", json={"citizen_id": "S9"}, headers=guest)
    account = {"X-Owner-Id": r.json()["owner_id"]}
    assert client.get("/api/state", headers=account).json()["step"] == 3
    assert any(
        d["data"].get("first_name") == "Gość"
        for d in client.get("/api/drafts", headers=account).json()
    )
    # Logging out and in again: the account keeps everything, the guest id is empty.
    assert client.get("/api/state", headers=guest).json()["form"] is None
    assert client.get("/api/state", headers=account).json()["form"] == {"stage": "born"}
