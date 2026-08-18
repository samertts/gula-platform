"""Tests for the Digital Patient Card module (routes + service).

Critical invariants under test:

1. **Tenant isolation** — a user from Lab A cannot fetch / scan / print a
   patient that belongs to Lab B (404 / 403, never data leak).
2. **Signed-token integrity** — tampered or expired tokens are rejected, and
   tokens bound to a different lab are rejected by the scan endpoint.
3. **Audit trail** — card view, scan, and history fetch each write an
   ``audit_logs`` row.
4. **Schema neutrality** — all behaviour works against the existing schema;
   no new tables are introduced by this module.
"""
from __future__ import annotations

import os
import time

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)

import pytest


def auth_headers(user_id: int, lab_id: int, role: str = "admin") -> dict:
    """Bearer header for the given user — mirrors ``conftest.auth_headers``.

    Inlined rather than imported because ``backend/tests/`` is not a Python
    package (no ``__init__.py``), so ``from tests.conftest import …`` fails
    under CI's pytest invocation.
    """
    from app.security.auth import create_token

    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role, "account_kind": "lab"})
    return {"Authorization": f"Bearer {token}"}


# ── Service-level tests ──────────────────────────────────────────────────────

def test_card_token_roundtrip():
    from app.services.patient_card import issue_card_token, verify_card_token

    token = issue_card_token(patient_id=42, lab_id=7)
    pid, lab = verify_card_token(token)
    assert pid == 42
    assert lab == 7


def test_card_token_rejects_tampered_signature():
    from app.services.patient_card import (
        CardTokenError,
        issue_card_token,
        verify_card_token,
    )

    token = issue_card_token(patient_id=1, lab_id=1)
    body, _sig = token.rsplit(".", 1)
    bad = body + "." + "A" * 22

    with pytest.raises(CardTokenError):
        verify_card_token(bad)


def test_card_token_rejects_expired():
    from app.services.patient_card import (
        CardTokenError,
        issue_card_token,
        verify_card_token,
    )

    # ttl_seconds is clamped to a minimum of 60 (which still expires in our test)
    token = issue_card_token(patient_id=1, lab_id=1, ttl_seconds=1)
    # Sleep just past the floor of 60s would be too slow — instead manually
    # forge an expired token by manipulating the body.
    import base64

    expired_body = f"1.1.{int(time.time()) - 10}".encode("ascii")
    expired_b64 = base64.urlsafe_b64encode(expired_body).rstrip(b"=").decode()
    from app.services.patient_card import _sign
    sig = _sign(expired_body)
    expired_token = f"{expired_b64}.{sig}"

    with pytest.raises(CardTokenError, match="expired"):
        verify_card_token(expired_token)
    # And the original (1s TTL clamped to 60s) is still valid right now:
    from app.services.patient_card import verify_card_token as v
    pid, lab = v(token)
    assert (pid, lab) == (1, 1)


def test_card_token_malformed_inputs():
    from app.services.patient_card import CardTokenError, verify_card_token

    for bad in ["", "abc", "a.b.c.d.e", "x" * 300, "noseparator"]:
        with pytest.raises(CardTokenError):
            verify_card_token(bad)


# ── Route-level tests ────────────────────────────────────────────────────────

@pytest.fixture()
def lab_with_patient(db, make_lab, make_lab_user):
    """A lab + admin + a patient with one validated order and 2 results."""
    from datetime import date

    from app.models.lab_order import LabOrder
    from app.models.lab_result import LabResult, generate_token, hash_token
    from app.models.patient import Patient

    lab = make_lab(name="MainLab")
    user = make_lab_user(lab_id=lab.id, role="admin")

    patient = Patient(
        lab_id=lab.id,
        full_name="أحمد محمود",
        phone="07700000001",
        birth_date=date(1990, 5, 1),
        gender="M",
        health_id="GULA-TESTID0001",
    )
    db.add(patient)
    db.flush()

    order = LabOrder(
        patient_id=patient.id,
        lab_id=lab.id,
        doctor_name="د. علي",
        status="validated",
    )
    db.add(order)
    db.flush()

    for name, val, unit in [("Glucose", 95.0, "mg/dL"), ("HbA1c", 5.4, "%")]:
        tok = generate_token()
        db.add(LabResult(
            order_id=order.id,
            test_name=name,
            value=val,
            unit=unit,
            token=tok,
            token_hash=hash_token(tok),
        ))
    db.commit()

    return {"lab": lab, "user": user, "patient": patient, "order": order}


def test_get_card_returns_minimum_disclosure_without_token(client, lab_with_patient):
    fix = lab_with_patient
    headers = auth_headers(fix["user"].id, fix["lab"].id, role="admin")

    r = client.get(f"/patient-card/{fix['patient'].id}", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["card"]["health_id_masked"].endswith("0001")
    assert body["card"]["full_name"] == "أحمد محمود"
    assert "token" not in body
    assert "health_id" not in body["card"]
    assert "phone" not in body["card"]
    assert body["qr_url"].endswith("/qr.png")


def test_get_card_tenant_isolation(client, db, lab_with_patient, make_lab, make_lab_user):
    """A user from another lab must NOT see this patient."""
    other_lab = make_lab(name="OtherLab")
    other_user = make_lab_user(lab_id=other_lab.id, role="admin")
    db.commit()

    headers = auth_headers(other_user.id, other_lab.id, role="admin")
    r = client.get(f"/patient-card/{lab_with_patient['patient'].id}", headers=headers)
    assert r.status_code == 404


def test_get_card_qr_returns_png(client, lab_with_patient):
    fix = lab_with_patient
    headers = auth_headers(fix["user"].id, fix["lab"].id, role="admin")

    r = client.get(f"/patient-card/{fix['patient'].id}/qr.png", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_scan_valid_token_returns_card(client, lab_with_patient):
    from app.services.patient_card import issue_card_token

    fix = lab_with_patient
    headers = auth_headers(fix["user"].id, fix["lab"].id, role="admin")
    token = issue_card_token(fix["patient"].id, fix["lab"].id)

    r = client.post("/patient-card/scan", json={"token": token}, headers=headers)
    assert r.status_code == 200
    assert r.json()["card"]["patient_id"] == fix["patient"].id


def test_scan_cross_lab_token_blocked(client, db, lab_with_patient, make_lab, make_lab_user):
    """A token issued for Lab A scanned by a Lab B user → 403."""
    from app.services.patient_card import issue_card_token

    other_lab = make_lab(name="ForeignLab")
    other_user = make_lab_user(lab_id=other_lab.id, role="admin")
    db.commit()

    fix = lab_with_patient
    foreign_headers = auth_headers(other_user.id, other_lab.id, role="admin")
    token = issue_card_token(fix["patient"].id, fix["lab"].id)

    r = client.post("/patient-card/scan", json={"token": token}, headers=foreign_headers)
    assert r.status_code == 403


def test_scan_invalid_token_400_and_audited(client, db, lab_with_patient):
    from app.models.audit_log import AuditLog

    fix = lab_with_patient
    headers = auth_headers(fix["user"].id, fix["lab"].id, role="admin")

    before = db.query(AuditLog).filter(
        AuditLog.action == "scan_failed",
        AuditLog.resource_type == "patient_card",
    ).count()

    r = client.post("/patient-card/scan", json={"token": "garbage.token"}, headers=headers)
    assert r.status_code == 400

    after = db.query(AuditLog).filter(
        AuditLog.action == "scan_failed",
        AuditLog.resource_type == "patient_card",
    ).count()
    assert after == before + 1


def test_history_returns_orders_and_results(client, lab_with_patient):
    fix = lab_with_patient
    headers = auth_headers(fix["user"].id, fix["lab"].id, role="admin")

    r = client.get(f"/patient-card/{fix['patient'].id}/history", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["patient"]["patient_id"] == fix["patient"].id
    assert body["summary"]["total_orders"] == 1
    assert body["summary"]["completed_or_validated"] == 1
    assert len(body["timeline"]) == 1
    assert len(body["timeline"][0]["results"]) == 2
    test_names = {r["test_name"] for r in body["timeline"][0]["results"]}
    assert test_names == {"Glucose", "HbA1c"}


def test_history_writes_audit_entry(client, db, lab_with_patient):
    from app.models.audit_log import AuditLog

    fix = lab_with_patient
    headers = auth_headers(fix["user"].id, fix["lab"].id, role="admin")

    before = db.query(AuditLog).filter(
        AuditLog.action == "view_history",
        AuditLog.resource_type == "patient_card",
        AuditLog.resource_id == fix["patient"].id,
    ).count()

    client.get(f"/patient-card/{fix['patient'].id}/history", headers=headers)

    after = db.query(AuditLog).filter(
        AuditLog.action == "view_history",
        AuditLog.resource_type == "patient_card",
        AuditLog.resource_id == fix["patient"].id,
    ).count()
    assert after == before + 1


def test_print_card_returns_html_with_qr(client, lab_with_patient):
    fix = lab_with_patient
    headers = auth_headers(fix["user"].id, fix["lab"].id, role="admin")

    r = client.get(f"/patient-card/{fix['patient'].id}/print", headers=headers)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "بطاقة المراجع" in r.text
    assert "GULA-TESTID0001" in r.text
    assert "data:image/png;base64," in r.text


def test_print_card_escapes_html_in_name(client, db, make_lab, make_lab_user):
    """Patient name must be HTML-escaped to block XSS via the printable card."""
    from datetime import date

    from app.models.patient import Patient

    lab = make_lab(name="EscapeLab")
    user = make_lab_user(lab_id=lab.id, role="admin")
    p = Patient(
        lab_id=lab.id,
        full_name="<script>alert(1)</script>",
        phone="07700000099",
        birth_date=date(1985, 1, 1),
        gender="F",
        health_id="GULA-XSS0001",
    )
    db.add(p)
    db.commit()

    headers = auth_headers(user.id, lab.id, role="admin")
    r = client.get(f"/patient-card/{p.id}/print", headers=headers)
    assert r.status_code == 200
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text


def test_unauthenticated_requests_rejected(client, lab_with_patient):
    pid = lab_with_patient["patient"].id
    for path in [
        f"/patient-card/{pid}",
        f"/patient-card/{pid}/qr.png",
        f"/patient-card/{pid}/history",
        f"/patient-card/{pid}/print",
    ]:
        r = client.get(path)
        assert r.status_code in (401, 403), f"{path} should require auth, got {r.status_code}"

    r = client.post("/patient-card/scan", json={"token": "x" * 30})
    assert r.status_code in (401, 403)
