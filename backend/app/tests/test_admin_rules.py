"""Rules edited in the admin panel: validation, dependencies, test run, reset."""

HEADERS = {"X-Admin-Token": "admin"}
PROFILE = {
    "child": {"birth_date": "2026-11-10"},
    "mother": {
        "employment": "employee",
        "average_monthly_base": 6000,
        "employer_insured_count": 50,
    },
}


def _rule(client, code):
    return next(
        r for r in client.get("/api/admin/rules", headers=HEADERS).json() if r["code"] == code
    )


def test_rules_need_admin_token(client):
    assert client.get("/api/admin/rules").status_code == 401


def test_rules_list_has_dependencies_and_sources(client):
    rule = _rule(client, "stawka_macierzynska")
    assert "usredniona" in rule["uses"] and "mama_macierzynski" in rule["used_by"]
    assert rule["parameters"] == ["rate_averaged", "rate_maternity"]
    assert rule["source"] == "UZ" and rule["in_seed"] and not rule["errors"]


def test_dictionary_lists_facts_functions_parameters(client):
    data = client.get("/api/admin/rules/dictionary", headers=HEADERS).json()
    assert any(f["path"] == "dziecko.martwe_urodzenie" for f in data["facts"])
    assert any(f["name"] == "dodaj_dni" for f in data["functions"])
    assert any(p["key"] == "rate_parental" for p in data["parameters"])
    assert "okres" in data["kinds"]


def test_validate_reports_unknown_names_and_cycles(client):
    bad = {"code": "nowa", "kind": "wartosc", "expression": "nie_ma_takiej + 1"}
    out = client.post("/api/admin/rules/validate", headers=HEADERS, json=bad).json()
    assert not out["ok"] and "nieznane dane" in out["errors"][0]
    cycle = {
        **_rule(client, "porod"),
        "expression": "dziecko.zdarzenie == 'porod' and zdarzenie_uprawnia",
    }
    out = client.post("/api/admin/rules/validate?replace=porod", headers=HEADERS, json=cycle).json()
    assert not out["ok"] and any("cykliczna" in e for e in out["errors"])


def test_change_rule_applies_to_calculation_and_reset(client):
    rule = _rule(client, "wylaczna_czesc_tyg")
    family = {**PROFILE, "father": {"employment": "employee", "average_monthly_base": 6000}}
    changed = client.put(
        "/api/admin/rules/wylaczna_czesc_tyg",
        headers=HEADERS,
        json={**rule, "expression": "10", "note": "test"},
    )
    assert changed.status_code == 200 and changed.json()["modified"]
    result = client.post("/api/rules/evaluate", json=family).json()
    father = sum(
        p["days"] for p in result["timeline"] if p["person"] == "father" and p["kind"] == "parental"
    )
    assert father == 70
    history = client.get("/api/admin/rules/wylaczna_czesc_tyg/history", headers=HEADERS).json()
    assert (
        history[0]["note"] == "test"
        and history[0]["data"]["expression"] == "param('parental_non_transferable_weeks')"
    )
    reset = client.post("/api/admin/rules/wylaczna_czesc_tyg/reset", headers=HEADERS).json()
    assert (
        reset["expression"] == "param('parental_non_transferable_weeks')" and not reset["modified"]
    )


def test_invalid_change_is_rejected(client):
    rule = _rule(client, "stawka_macierzynska")
    response = client.put(
        "/api/admin/rules/stawka_macierzynska",
        headers=HEADERS,
        json={**rule, "expression": "param('nie_ma')"},
    )
    assert response.status_code == 422
    assert "brak parametru" in response.json()["detail"]["errors"][0]


def test_create_test_and_delete_new_rule(client):
    new = {
        "code": "r_test_wysoka_podstawa",
        "kind": "ryzyko",
        "severity": "info",
        "condition": "mama_podstawa > 5000",
        "title_pl": "Wysoka podstawa",
        "text_pl": "Podstawa {mama_podstawa} zł.",
        "source": "UZ",
    }
    trial = client.post(
        "/api/admin/rules/test", headers=HEADERS, json={"profile": PROFILE, "draft": new}
    ).json()
    assert trial["ok"] and any(
        r["code"] == "r_test_wysoka_podstawa" for r in trial["result"]["risks"]
    )
    assert trial["values"]["mama_podstawa"] == 5177.4
    created = client.post("/api/admin/rules", headers=HEADERS, json=new)
    assert created.status_code == 201
    risks = client.post("/api/rules/evaluate", json=PROFILE).json()["risks"]
    assert any(r["text_pl"] == "Podstawa 5 177,4 zł." for r in risks)
    assert (
        client.delete("/api/admin/rules/r_test_wysoka_podstawa", headers=HEADERS).status_code == 204
    )
    assert client.delete("/api/admin/rules/porod", headers=HEADERS).status_code == 409


def test_test_run_reports_plan_violation(client):
    body = {
        "profile": {
            **PROFILE,
            "child": {"due_date": "2027-03-01"},
            "plan": {"maternity_before_birth_weeks": 8},
        }
    }
    out = client.post("/api/admin/rules/test", headers=HEADERS, json=body).json()
    assert not out["ok"] and "6 tygodni" in out["violation"]


def test_graph_edges(client):
    graph = client.get("/api/admin/rules/graph", headers=HEADERS).json()
    assert ["porod", "zdarzenie_uprawnia"] in graph["edges"]
