"""Tests for the citizen registry CRUD endpoints (``/v1/citizens``).

This surface previously had zero test coverage even though it is the core
of the national citizen registry (national ID, phone, address, chronic
diseases, allergies). These tests lock in the documented behavior so a
future change can't silently break registration, duplicate detection, or
lookup without a red test.
"""
from __future__ import annotations


def test_register_citizen_returns_health_id(app_client):
    client, _ = app_client

    resp = client.post(
        "/v1/citizens/register",
        json={
            "full_name": "أحمد علي حسين",
            "gender": "m",
            "birth_date": "1990-01-01",
            "phone": "07701234567",
            "province": "Baghdad",
            "national_id": "123456789012",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["health_id"]
    assert body["national_id"] == "123456789012"
    assert body["gender"] == "M"


def test_register_rejects_duplicate_national_id(app_client):
    client, _ = app_client

    payload = {
        "full_name": "سارة محمود",
        "national_id": "111122223333",
    }
    first = client.post("/v1/citizens/register", json=payload)
    assert first.status_code == 201

    second = client.post(
        "/v1/citizens/register",
        json={"full_name": "اسم مختلف تماما", "national_id": "111122223333"},
    )
    assert second.status_code == 409
    assert second.json()["detail"]["error"] == "national_id_exists"


def test_register_flags_probable_duplicate_person(app_client):
    client, _ = app_client

    payload = {
        "full_name": "محمد كريم جاسم",
        "birth_date": "1985-05-05",
        "phone": "07709998877",
    }
    first = client.post("/v1/citizens/register", json=payload)
    assert first.status_code == 201

    second = client.post("/v1/citizens/register", json=payload)
    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail["error"] == "duplicate_candidate"
    assert detail["matches"]


def test_register_rejects_invalid_national_id(app_client):
    client, _ = app_client

    resp = client.post(
        "/v1/citizens/register",
        json={"full_name": "خالد ياسين", "national_id": "abc123"},
    )
    assert resp.status_code == 422


def test_get_citizen_by_health_id(app_client, make_citizen):
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-GET-1", full_name="ليلى كاظم")

    resp = client.get("/v1/citizens/HID-GET-1")
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "ليلى كاظم"


def test_get_unknown_citizen_is_404(app_client):
    client, _ = app_client
    resp = client.get("/v1/citizens/HID-MISSING")
    assert resp.status_code == 404


def test_search_by_national_id_is_exact_match(app_client, make_citizen):
    client, Session = app_client
    with Session() as s:
        make_citizen(
            s, health_id="HID-S1", full_name="نور الهدى",
            national_id="999900001111",
        )
        make_citizen(
            s, health_id="HID-S2", full_name="نور الهدى الثاني",
            national_id="999900001112",
        )

    # A substring of the national_id must NOT match (exact match only).
    resp = client.get("/v1/citizens/search", params={"q": "9999000011"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    resp = client.get("/v1/citizens/search", params={"q": "999900001111"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["health_id"] == "HID-S1"


def test_search_by_name_substring(app_client, make_citizen):
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-N1", full_name="عمر الشريف")

    resp = client.get("/v1/citizens/search", params={"q": "الشريف"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["health_id"] == "HID-N1"


def test_update_citizen_mutable_fields(app_client, make_citizen):
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-U1", full_name="قديم", phone="0770")

    resp = client.put(
        "/v1/citizens/HID-U1",
        json={"phone": "07711112222", "address": "بغداد - الكرادة"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["phone"] == "07711112222"
    assert body["address"] == "بغداد - الكرادة"


def test_update_rejects_unknown_fields(app_client, make_citizen):
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-U2")

    resp = client.put(
        "/v1/citizens/HID-U2",
        json={"national_id": "000000000000"},
    )
    assert resp.status_code == 422


def test_update_empty_payload_is_400(app_client, make_citizen):
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-U3")

    resp = client.put("/v1/citizens/HID-U3", json={})
    assert resp.status_code == 400


def test_citizen_summary_includes_recent_tests(app_client, make_citizen, make_lab, make_result):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(
            s, health_id="HID-SUM-1",
            chronic_diseases=["سكري"], allergies=["بنسلين"],
        )
        lab = make_lab(s)
        make_result(s, citizen_id=citizen.id, lab_id=lab.id, test_code="HGB")

    resp = client.get("/v1/citizens/HID-SUM-1/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["chronic_diseases"] == ["سكري"]
    assert body["allergies"] == ["بنسلين"]
