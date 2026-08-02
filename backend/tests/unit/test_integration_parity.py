"""PROGRAM-INTEGRATION-OMEGA-002 — Frontend↔Backend contract parity tests.

Covers the endpoints added/aligned to close the frontend integration gaps:
  1. GET /health, /health/ready (public), /health/status, /health/deep (auth)
  2. GET /api/ai/stats + /api/ai/export (AI telemetry contract)
  3. GET /ehr/patient/{id} + /ehr/patient/{id}/summary (EHR composite contract)

Each test asserts the exact response shape the frontend types expect, so a
backend refactor that breaks the frontend contract fails CI.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

import pytest
from app._compat import UTC
from tests.conftest import auth_headers


@pytest.fixture()
def now_utc():
    return datetime.now(UTC)


# ═══════════════════════════════════════════════════════════════════════════
# Health endpoints (frontend HealthStatus / DeepHealth contract)
# ═══════════════════════════════════════════════════════════════════════════


class TestHealthEndpoints:
    def test_health_liveness_public_and_shape(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("ok", "degraded")
        assert body["platform"] == "GULA Platform"
        assert body["platform_ar"]
        assert body["version"]
        assert body["environment"]
        assert isinstance(body["system_ready"], bool)
        assert body["database"]
        assert isinstance(body["degraded_mode"], bool)
        assert isinstance(body["degradation_level"], int)

    def test_health_ready_public(self, client):
        r = client.get("/health/ready")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body["system_ready"], bool)
        assert "database" in body

    def test_health_status_public(self, client):
        r = client.get("/health/status")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("ok", "degraded")
        assert isinstance(body["system_ready"], bool)

    def test_health_deep_public(self, client):
        r = client.get("/health/deep")
        assert r.status_code == 200

    def test_health_status_authenticated_shape(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.get("/health/status", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("ok", "degraded")
        assert isinstance(body["system_ready"], bool)

    def test_health_deep_shape(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.get("/health/deep", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["grade"] in ("A", "B", "C", "F")
        assert isinstance(body["issues"], list)
        comps = body["components"]
        assert set(comps) == {"database", "redis", "queue"}
        assert comps["database"]["ok"] is True
        assert isinstance(comps["database"]["latency_ms"], float)
        assert isinstance(comps["queue"]["backlog"], int)
        proc = body["process"]
        assert isinstance(proc["memory_rss_mb"], float)
        assert isinstance(proc["uptime_s"], int)
        assert isinstance(proc["uptime_h"], float)
        assert isinstance(proc["active_requests"], int)
        assert isinstance(proc["degraded_mode"], bool)


# ═══════════════════════════════════════════════════════════════════════════
# AI telemetry contract (frontend aiTelemetryApi)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def seeded_ai_data(db, make_lab, make_lab_user):
    from app.models.ai_interaction import AIFeedback, AIInteraction, AIUnresolvedQuestion

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id)
    other_lab = make_lab()
    other_user = make_lab_user(lab_id=other_lab.id)

    _now = datetime.now(UTC)
    db.add(
        AIInteraction(
            id=uuid.uuid4(),
            lab_id=lab.id,
            anonymous_session_id="session-a",
            prompt="interpret glucose",
            response="ok",
            status="ok",
            safety_flags=["pii_detected"],
            created_at=_now,
        )
    )
    db.add(
        AIInteraction(
            id=uuid.uuid4(),
            lab_id=lab.id,
            anonymous_session_id="session-b",
            status="error",
            error_code="provider_timeout",
            safety_flags=None,
            created_at=_now,
        )
    )
    db.add(
        AIInteraction(
            id=uuid.uuid4(),
            lab_id=other_lab.id,
            anonymous_session_id="session-other",
            status="ok",
            safety_flags=["policy_violation"],
            created_at=_now,
        )
    )
    db.add(
        AIUnresolvedQuestion(
            id=uuid.uuid4(),
            lab_id=lab.id,
            anonymous_session_id="session-a",
            question="what is CRP?",
            status="open",
            created_at=_now,
        )
    )
    db.commit()

    db.add(
        AIFeedback(
            id=uuid.uuid4(),
            interaction_id=db.query(AIInteraction.id)
            .filter(AIInteraction.lab_id == lab.id)
            .first()[0],
            lab_id=lab.id,
            anonymous_session_id="session-a",
            signal="helpful",
            created_at=_now,
        )
    )
    db.commit()
    return lab, user, other_lab, other_user


class TestAiTelemetryStats:
    def test_stats_tenant_scoped(self, client, seeded_ai_data):
        lab, user, _other_lab, _other_user = seeded_ai_data
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.get("/api/ai/stats", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body == {
            "total_interactions": 2,
            "total_feedback": 1,
            "total_unresolved": 1,
            "total_safety_flags": 1,
        }

    def test_stats_isolated_lab(self, client, seeded_ai_data):
        _lab, _user, other_lab, other_user = seeded_ai_data
        headers = auth_headers(other_user.id, other_lab.id, other_user.role)
        r = client.get("/api/ai/stats", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_interactions"] == 1
        assert body["total_feedback"] == 0
        assert body["total_unresolved"] == 0
        assert body["total_safety_flags"] == 1

    def test_stats_requires_auth(self, client):
        r = client.get("/api/ai/stats")
        assert r.status_code in (401, 403)


class TestAiTelemetryExport:
    def test_export_csv(self, client, seeded_ai_data):
        lab, user, _other_lab, _other_user = seeded_ai_data
        headers = auth_headers(user.id, lab.id, "admin")
        r = client.get("/api/ai/export", params={"format": "csv"}, headers=headers)
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        assert "id," in r.text
        assert "session-a" in r.text
        assert "session-other" not in r.text

    def test_export_json(self, client, seeded_ai_data):
        lab, user, _other_lab, _other_user = seeded_ai_data
        headers = auth_headers(user.id, lab.id, "admin")
        r = client.get("/api/ai/export", params={"format": "json"}, headers=headers)
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]
        body = r.json()
        assert body["count"] == 2
        assert body["lab_id"] == lab.id

    def test_export_forbidden_for_technician(
        self, client, db, make_lab, make_lab_user, seeded_ai_data
    ):
        lab, _user, _other_lab, _other_user = seeded_ai_data
        tech_user = make_lab_user(lab_id=lab.id, role="technician")
        headers = auth_headers(tech_user.id, lab.id, "technician")
        r = client.get("/api/ai/export", headers=headers)
        assert r.status_code == 403

    def test_export_invalid_format_rejected(self, client, seeded_ai_data):
        lab, user, _other_lab, _other_user = seeded_ai_data
        headers = auth_headers(user.id, lab.id, "admin")
        r = client.get("/api/ai/export", params={"format": "xml"}, headers=headers)
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# EHR composite contract (frontend ehrApi getPatientEhr / getPatientSummary)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def national_patient(db, make_lab, make_lab_user):
    from app.national.domain.patient import Patient
    from app.national.enums import Gender

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id)
    patient = Patient(
        lab_id=lab.id,
        health_number="HN-TEST-001",
        first_name="Ali",
        last_name="Ahmed",
        full_name="Ali Ahmed",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.MALE,
        phone="07701234567",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return lab, user, patient


class TestEhrComposite:
    def test_get_patient_ehr_shape(self, client, db, national_patient):
        lab, user, patient = national_patient
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.get(f"/ehr/patient/{patient.id}", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["patient"]["id"] == patient.id
        assert body["patient"]["full_name"] == "Ali Ahmed"
        assert body["patient"]["health_id"] == "HN-TEST-001"
        assert body["patient"]["gender"] == "male"
        assert isinstance(body["clinical_notes"], list)
        assert isinstance(body["conditions"], list)
        assert isinstance(body["medications"], list)
        assert isinstance(body["allergies"], list)
        assert isinstance(body["immunizations"], list)

    def test_get_patient_summary_shape(self, client, db, national_patient):
        lab, user, patient = national_patient
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.get(f"/ehr/patient/{patient.id}/summary", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["patient_id"] == patient.id
        assert body["patient_name"] == "Ali Ahmed"
        assert body["health_id"] == "HN-TEST-001"
        assert body["age"] is not None
        assert body["gender"] == "male"
        assert isinstance(body["active_allergies"], list)
        assert isinstance(body["active_conditions"], list)
        assert isinstance(body["current_medications"], list)

    def test_patient_tenancy_enforced(self, client, db, make_lab, make_lab_user, national_patient):
        _lab, _user, patient = national_patient
        other_lab = make_lab()
        other_user = make_lab_user(lab_id=other_lab.id)
        headers = auth_headers(other_user.id, other_lab.id, other_user.role)
        r = client.get(f"/ehr/patient/{patient.id}", headers=headers)
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# Admin workflows contract (frontend AdminPages: pending labs, kill switch,
# control layer, log level)
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminWorkflows:
    def test_pending_labs_list_and_activate(self, client, db, make_lab, make_lab_user):
        pending = make_lab(name="Pending Lab", is_active=False)
        active = make_lab(name="Active Lab", is_active=True)
        user = make_lab_user(lab_id=active.id, role="master_admin")
        headers = auth_headers(user.id, active.id, user.role)

        r = client.get("/admin/labs/pending", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        names = [lab["name"] for lab in body["pending_labs"]]
        assert "Pending Lab" in names
        assert "Active Lab" not in names
        assert body["pending_labs"][0]["id"] == pending.id
        assert body["pending_labs"][0]["created_at"] is not None

        r = client.put(f"/admin/labs/{pending.id}/activate", headers=headers)
        assert r.status_code == 200
        r = client.get("/admin/labs/pending", headers=headers)
        assert all(lab["id"] != pending.id for lab in r.json()["pending_labs"])

    def test_pending_labs_forbidden_for_technician(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="technician")
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.get("/admin/labs/pending", headers=headers)
        assert r.status_code == 403

    def test_kill_switch_cycle(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="master_admin")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/admin/kill-switch/status", headers=headers)
        assert r.status_code == 200
        assert r.json()["active"] is False

        r = client.post(
            "/admin/kill-switch/activate", json={"reason": "test drill"}, headers=headers
        )
        assert r.status_code == 200
        r = client.get("/admin/kill-switch/status", headers=headers)
        assert r.json()["active"] is True
        assert r.json().get("reason") == "test drill"

        r = client.post(
            "/admin/kill-switch/deactivate", json={"reason": "all clear"}, headers=headers
        )
        assert r.status_code == 200
        r = client.get("/admin/kill-switch/status", headers=headers)
        assert r.json()["active"] is False

    def test_kill_switch_forbidden_for_technician(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="technician")
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.post("/admin/kill-switch/activate", json={"reason": "x"}, headers=headers)
        assert r.status_code == 403

    def test_control_layer_stats_shape(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="master_admin")
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.get("/admin/control-layer/stats", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert "policy" in body
        assert isinstance(body["policy"]["blocked_total"], int)
        assert isinstance(body["policy"]["allowed_total"], int)
        assert isinstance(body["policy"]["enabled"], bool)
        assert isinstance(body["auto_repair"], dict)

    def test_log_level_get_set(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="master_admin")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/admin/log-level", headers=headers)
        assert r.status_code == 200
        assert "root_level" in r.json()
        assert "effective_level" in r.json()

        r = client.post("/admin/log-level", json={"level": "DEBUG"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["new_level"] == "DEBUG"

        r = client.post("/admin/log-level", json={"level": "BOGUS"}, headers=headers)
        assert r.status_code == 400

    def test_log_level_forbidden_for_technician(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="technician")
        headers = auth_headers(user.id, lab.id, user.role)
        r = client.post("/admin/log-level", json={"level": "DEBUG"}, headers=headers)
        assert r.status_code == 403


class TestServiceAccounts:
    def test_create_list_rotate_revoke_cycle(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="master_admin")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.post(
            "/service-accounts",
            json={"name": "external-integration", "roles": ["staff"]},
            headers=headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "external-integration"
        assert body["api_key"]
        account_id = body["id"]

        r = client.get("/service-accounts", headers=headers)
        assert r.status_code == 200
        accounts = r.json()
        assert isinstance(accounts, list)
        found = [a for a in accounts if a["id"] == account_id]
        assert found
        assert found[0]["name"] == "external-integration"
        assert found[0]["is_active"] is True
        assert "api_key" not in found[0]

        r = client.post(f"/service-accounts/{account_id}/rotate", headers=headers)
        assert r.status_code == 200
        assert r.json()["api_key"]

        r = client.delete(f"/service-accounts/{account_id}", headers=headers)
        assert r.status_code == 200
        r = client.get("/service-accounts", headers=headers)
        revoked = [a for a in r.json() if a["id"] == account_id]
        assert revoked and revoked[0]["is_active"] is False

    def test_forbidden_for_technician(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="technician")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/service-accounts", headers=headers)
        assert r.status_code == 403
        r = client.post(
            "/service-accounts", json={"name": "x", "roles": ["staff"]}, headers=headers
        )
        assert r.status_code == 403
        r = client.delete("/service-accounts/1", headers=headers)
        assert r.status_code == 403


class TestGovernanceAuthorities:
    def test_authority_get_activate_suspend(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="master_admin")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.post(
            "/niam/governance/authorities",
            params={"authority_id": "AUTH-TEST-1", "name_en": "Author A"},
            headers=headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["authority_id"] == "AUTH-TEST-1"
        assert body["status"]
        authority_id = body["authority_id"]

        r = client.get(f"/niam/governance/authorities/{authority_id}", headers=headers)
        assert r.status_code == 200

        r = client.post(f"/niam/governance/authorities/{authority_id}/suspend", headers=headers)
        assert r.status_code == 200
        r = client.post(f"/niam/governance/authorities/{authority_id}/activate", headers=headers)
        assert r.status_code == 200

        r = client.put(f"/niam/governance/authorities/{authority_id}", json={}, headers=headers)
        assert r.status_code == 405


class TestMobileAppInfo:
    def test_mobile_app_info_route(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="staff")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/auth/mobile/app-info", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), dict)


class TestMfaWorkflow:
    def test_mfa_status_and_devices_shape(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="staff")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/mfa/status", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert set(body.keys()) == {"mfa_enabled", "devices"}
        assert body["mfa_enabled"] is False
        assert body["devices"] == []

        r = client.get("/mfa/devices", headers=headers)
        assert r.status_code == 200
        assert r.json() == body

    def test_totp_setup_verify_cycle(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="staff")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.post("/mfa/totp/setup", json={"device_name": "Phone"}, headers=headers)
        assert r.status_code == 200
        setup = r.json()
        assert setup["secret"]
        assert setup["uri"].startswith("otpauth://")
        assert len(setup["backup_codes"]) > 0
        assert setup["device_id"] > 0

        r = client.post("/mfa/totp/verify", json={"token": "123456"}, headers=headers)
        assert r.status_code in (400, 200)

        r = client.get("/mfa/status", headers=headers)
        assert r.json()["devices"][0]["device_name"] == "Phone"
        assert r.json()["devices"][0]["device_type"] == "totp"

        r = client.delete(f"/mfa/devices/{setup['device_id']}", headers=headers)
        assert r.status_code == 200
        assert r.json() == {"success": True}
        r = client.get("/mfa/status", headers=headers)
        assert r.json()["devices"] == []

    def test_mfa_requires_auth(self, client):
        r = client.get("/mfa/status")
        assert r.status_code == 401


class TestComplianceShapes:
    def test_audit_summary_shape(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="quality_manager")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/compliance/audit-summary", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert "lab_id" in body
        assert "total_audit_events" in body
        assert isinstance(body["actions_breakdown"], dict)
        assert "report_generated_at" in body

    def test_system_status_admin_shape(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="admin")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/compliance/system-status", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["dashboard"] == "GULA System Status"
        assert body["environment"] in ("production", "development")
        assert body["services"]["database"]["status"] in ("pass", "fail", "unknown")
        assert body["services"]["api"]["status"] in ("pass", "fail", "unknown")
        assert isinstance(body["compliance_checklist"], dict)
        assert isinstance(body["alerts"], list)

    def test_system_status_forbidden_for_technician(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="technician")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/compliance/system-status", headers=headers)
        assert r.status_code == 403


class TestAuditLogs:
    def test_audit_logs_shape(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="admin")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/admin/audit-logs", params={"limit": 10}, headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert isinstance(body["logs"], list)
        for log in body["logs"]:
            assert set(log.keys()) >= {"id", "action", "resource_type", "user_id", "created_at"}

    def test_audit_logs_forbidden_for_technician(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="technician")
        headers = auth_headers(user.id, lab.id, user.role)

        r = client.get("/admin/audit-logs", headers=headers)
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# PROGRAM-06 — Frontend route parity gate
# Every path in frontend-v3/src/api/endpoints.ts must resolve to a live
# backend route (method + path pattern). A frontend change that calls a
# non-existent endpoint fails CI.
# ═══════════════════════════════════════════════════════════════════════════


class TestFrontendRouteParity:
    @staticmethod
    def _frontend_paths():
        import re
        from pathlib import Path

        fe_file = (
            Path(__file__).resolve().parents[3] / "frontend-v3" / "src" / "api" / "endpoints.ts"
        )
        if not fe_file.exists():
            pytest.skip("frontend-v3 endpoints.ts not present")
        src = fe_file.read_text(encoding="utf-8")
        pat = re.compile(r"api\.(get|post|put|delete|patch)(?:<[^>]*>)?\(\s*([`\"'])([^`\"']+)\2")
        out = []
        for m in pat.finditer(src):
            norm = re.sub(r"\$\{[^}]*\}", "{id}", m.group(3)).split("?")[0]
            out.append((m.group(1).upper(), norm))
        return sorted(set(out))

    @staticmethod
    def _matches(fe_path: str, be_path: str) -> bool:
        import re

        fe_re = re.escape(fe_path).replace(r"\{id\}", "[^/]+")
        be_re = re.escape(be_path).replace(r"\{[^}]+\}", "[^/]+")
        return re.fullmatch(fe_re, be_path) is not None or re.fullmatch(be_re, fe_path) is not None

    def test_every_frontend_path_exists_on_backend(self, client):
        from fastapi.routing import _IncludedRouter

        be = []
        for r in client.app.routes:
            items = r.original_router.routes if isinstance(r, _IncludedRouter) else [r]
            for rr in items:
                for m in getattr(rr, "methods", None) or []:
                    if m != "HEAD":
                        be.append((m, getattr(rr, "path", "")))

        missing = []
        for method, path in self._frontend_paths():
            if not any(method == m and self._matches(path, bp) for m, bp in be):
                missing.append(f"{method} {path}")
        assert not missing, "frontend calls to non-existent backend routes:\n" + "\n".join(missing)
