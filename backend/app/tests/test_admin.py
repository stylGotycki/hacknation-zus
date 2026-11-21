from datetime import date

ADMIN = {"X-Admin-Token": "admin"}
FUTURE = "2099-01-01"


def test_admin_requires_token(client):
    assert client.get("/api/admin/parameters").status_code == 401
    assert client.get("/api/admin/parameters", headers={"X-Admin-Token": "x"}).status_code == 401
    assert client.get("/api/admin/check", headers=ADMIN).json() == {"ok": True}


def test_new_version_closes_previous_and_engine_uses_it(client):
    rows = client.get("/api/admin/parameters", headers=ADMIN).json()
    key = "rate_maternity"
    current = next(r for r in rows if r["key"] == key and r["current"])
    new_value = round(current["value"] - 0.1, 2)
    r = client.post(
        f"/api/admin/parameters/{key}/versions",
        json={"value": new_value, "valid_from": FUTURE},
        headers=ADMIN,
    )
    assert r.status_code == 201
    old = client.get(f"/api/parameters/{key}?date=2098-12-31").json()
    assert old["value"] == current["value"] and old["valid_to"] == "2098-12-31"
    assert client.get(f"/api/parameters/{key}?date={FUTURE}").json()["value"] == new_value
    # Not allowed: an earlier date, a different type.
    early = client.post(f"/api/admin/parameters/{key}/versions", json={"value": 1, "valid_from": "2020-01-01"}, headers=ADMIN)
    assert early.status_code == 409
    wrong = client.post(f"/api/admin/parameters/{key}/versions", json={"value": "x", "valid_from": "2100-01-01"}, headers=ADMIN)
    assert wrong.status_code == 422


def test_seed_keeps_admin_versions_and_delete_restores(client):
    from app.core.db import SessionLocal
    from app.seed import seed_parameters

    with SessionLocal() as db:
        seed_parameters(db)
    key = "rate_maternity"
    assert client.get(f"/api/parameters/{key}?date={FUTURE}").json()["value"] < 1.0
    assert client.delete(f"/api/admin/parameters/{key}/versions/{FUTURE}", headers=ADMIN).status_code == 204
    restored = client.get(f"/api/parameters/{key}?date={FUTURE}").json()
    assert restored["valid_to"] is None
    seed_row = next(r for r in client.get("/api/admin/parameters", headers=ADMIN).json() if r["key"] == key and r["from_seed"])
    assert client.delete(f"/api/admin/parameters/{key}/versions/{seed_row['valid_from']}", headers=ADMIN).status_code == 409


def test_table_parameter_keeps_keys(client):
    key = "care_allowance_limits_days"
    current = next(r for r in client.get("/api/admin/parameters", headers=ADMIN).json() if r["key"] == key and r["current"])
    bad = {**current["value"]}
    bad.pop("other")
    assert client.post(f"/api/admin/parameters/{key}/versions", json={"value": bad, "valid_from": FUTURE}, headers=ADMIN).status_code == 422
    assert date.fromisoformat(current["valid_from"]) < date.fromisoformat(FUTURE)


def test_admin_sets_application_status_with_note(client):
    owner = {"X-Owner-Id": "admin-test"}
    data = {"first_name": "A", "last_name": "B", "pesel": "1", "employer_name": "C", "leave_start": "2026-12-01",
            "leave_end": "2026-12-14", "child_date": "2026-11-30", "declaration": True}
    app_id = client.post("/api/applications", json={"form_code": "leave_paternity", "data": data}, headers=owner).json()["id"]
    listed = client.get("/api/admin/applications", headers=ADMIN).json()
    assert any(a["id"] == app_id and a["owner_id"] == "admin-test" for a in listed)
    r = client.post(f"/api/admin/applications/{app_id}/status", json={"status": "decided", "note": "Przyznano"}, headers=ADMIN)
    assert r.json() == {"status": "decided"}
    history = client.get("/api/applications", headers=owner).json()[0]["history"]
    assert history[-1]["note"] == "Przyznano"
    assert client.post(f"/api/admin/applications/{app_id}/status", json={"status": "zzz"}, headers=ADMIN).status_code == 422
