"""AUD-PRV-003 — force_create duplicate override must be authorized + audited.

The auditor found ``force_create`` (client-controlled) skipped ALL duplicate
detection with no permission check, no reason and no audit, so any authenticated
user could silently create duplicate patient records.

The fix: the route requires the elevated ``patients:delete`` permission and a
documented reason (min 10 chars), denies+audits unauthorized attempts; the
service adds defense-in-depth validation, audits successful overrides, and
refuses an exact same-facility national-ID collision (must go through MPI merge).

Falsification axes:
1. Unauthorized role cannot force_create (403) and denial is audited.
2. Authorized role without a valid reason cannot force_create (422).
3. Authorized + reasoned override succeeds and is audited with the reason.
4. Service rejects reason-less override even when called directly (defense in depth).
5. Exact same-lab NID collision is refused (409) — no silent duplicate persisted.
6. Normal (non-force) creation is unaffected.
"""
from __future__ import annotations

import pytest
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.services.identity import hash_national_id
from app.services.patient_service import create_patient

VALID_NID = "123456789012"
REASON = "Two distinct siblings share a phone number; verified by civil registry"


def _login(client, user):
    resp = client.post("/login", json={"email": user.email, "password": "Testpass1"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _create_payload(**overrides):
    body = {"full_name": "Test Patient", "phone": "+9647700000000"}
    body.update(overrides)
    return body


class TestForceCreateRouteGate:
    def test_unauthorized_role_denied_and_audited(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab.id, role="doctor")  # read-only patient permission
        token = _login(client, user)
        resp = client.post(
            "/patients",
            headers={"Authorization": f"Bearer {token}"},
            json=_create_payload(force_create=True, force_reason=REASON),
        )
        assert resp.status_code == 403, resp.text
        denial = db.query(AuditLog).filter(AuditLog.action == "patient_duplicate_override_denied").first()
        assert denial is not None, "unauthorized override attempt was not audited"

    @pytest.mark.parametrize("reason", [None, "", "short", "   too short   "])
    def test_authorized_but_missing_or_short_reason_denied(self, client, db, make_lab, make_lab_user, reason):
        lab = make_lab()
        user = make_lab_user(lab.id, role="admin")  # has patients:delete
        token = _login(client, user)
        body = _create_payload(force_create=True)
        if reason is not None:
            body["force_reason"] = reason
        resp = client.post("/patients", headers={"Authorization": f"Bearer {token}"}, json=body)
        assert resp.status_code == 422, resp.text

    def test_authorized_with_reason_succeeds_and_is_audited(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab.id, role="admin")
        token = _login(client, user)
        resp = client.post(
            "/patients",
            headers={"Authorization": f"Bearer {token}"},
            json=_create_payload(force_create=True, force_reason=REASON, national_id=VALID_NID),
        )
        assert resp.status_code == 201, resp.text
        audit = db.query(AuditLog).filter(AuditLog.action == "patient_duplicate_override").first()
        assert audit is not None, "successful override was not audited"
        assert REASON[:20] in audit.details

    def test_normal_creation_does_not_require_reason(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab.id, role="technician")
        token = _login(client, user)
        resp = client.post(
            "/patients",
            headers={"Authorization": f"Bearer {token}"},
            json=_create_payload(national_id=VALID_NID),
        )
        assert resp.status_code == 201, resp.text


class TestForceCreateServiceDefense:
    def _svc(self, db, lab_id, **overrides):
        args = {
            "db": db, "lab_id": lab_id, "user_id": 1, "user_role": "admin",
            "full_name": "Test Patient", "phone": "+9647700000000",
        }
        args.update(overrides)
        return create_patient(**args)

    def test_service_rejects_reasonless_override(self, db, make_lab):
        lab = make_lab()
        result = self._svc(db, lab.id, force_create=True, force_reason=None)
        assert result["status_code"] == 422

    def test_service_refuses_exact_same_lab_nid_collision(self, db, make_lab):
        """No second record for the same NID at the same facility via force_create."""
        lab = make_lab()
        nid_hash = hash_national_id(VALID_NID)
        db.add(Patient(lab_id=lab.id, full_name="Existing", phone="+9647700000000",
                       national_id_hash=nid_hash))
        db.commit()
        before = db.query(Patient).filter(Patient.lab_id == lab.id).count()
        result = self._svc(db, lab.id, force_create=True, force_reason=REASON,
                           national_id=VALID_NID)
        assert result["status_code"] == 409
        after = db.query(Patient).filter(Patient.lab_id == lab.id).count()
        assert after == before, "force_create silently persisted a duplicate NID record"

    def test_service_allows_legitimate_override_with_reason(self, db, make_lab):
        lab = make_lab()
        result = self._svc(db, lab.id, force_create=True, force_reason=REASON,
                           national_id=VALID_NID)
        assert "patient" in result, result
        assert result["patient"]["full_name"] == "Test Patient"
        audit = db.query(AuditLog).filter(AuditLog.action == "patient_duplicate_override").first()
        assert audit is not None and REASON[:20] in audit.details
