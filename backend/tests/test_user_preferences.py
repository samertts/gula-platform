"""Security regression tests for Phase 21 user preferences."""

from app.models.audit_log import AuditLog
from app.routes.user_preferences import AccessibilityPreferences
from app.security.auth import create_token
from sqlalchemy import text


def _headers(user_id: int, lab_id: int, role: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token({'user_id': user_id, 'lab_id': lab_id, 'role': role})}"}


def test_accessibility_defaults_are_presentation_only(client, db, make_lab, make_lab_user):
    lab = make_lab("Accessibility Lab")
    user = make_lab_user(lab.id, role="admin")

    response = client.get("/user-preferences/accessibility", headers=_headers(user.id, lab.id))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "default"
    assert body["version"] == 0
    assert body["high_contrast"] is False
    assert body["reduced_color_dependence"] is True


def test_health_preferences_require_explicit_consent(client, db, make_lab, make_lab_user):
    lab = make_lab("Health Preferences Lab")
    user = make_lab_user(lab.id, role="admin")

    response = client.put(
        "/user-preferences/health",
        headers=_headers(user.id, lab.id),
        json={
            "preferences": {"allergies": ["penicillin"]},
            "consent": False,
            "consent_version": "health-v1",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Request failed."


def test_health_preferences_are_encrypted_and_audited(client, db, make_lab, make_lab_user):
    lab = make_lab("Encrypted Health Lab")
    user = make_lab_user(lab.id, role="admin")
    payload = {
        "allergies": ["penicillin"],
        "chronic_conditions": ["asthma"],
        "communication_needs": "Arabic",
    }

    saved = client.put(
        "/user-preferences/health",
        headers=_headers(user.id, lab.id),
        json={
            "preferences": payload,
            "consent": True,
            "consent_version": "health-v1",
        },
    )

    assert saved.status_code == 200
    assert saved.json()["preferences"] == {**payload, "emergency_assistance_preferences": None, "other_health_considerations": None}
    row = db.execute(text("SELECT encrypted_payload FROM health_preferences WHERE user_id = :user_id"), {"user_id": user.id}).fetchone()
    assert row is not None
    assert "penicillin" not in row[0]
    audit_rows = db.query(AuditLog).filter(AuditLog.user_id == user.id, AuditLog.resource_type == "user_preferences").all()
    assert audit_rows
    assert all("penicillin" not in (entry.details or "") for entry in audit_rows)


def test_updates_require_current_version(client, make_lab, make_lab_user):
    lab = make_lab("Versioned Preferences Lab")
    user = make_lab_user(lab.id, role="admin")
    headers = _headers(user.id, lab.id)

    first = client.put(
        "/user-preferences/accessibility",
        headers=headers,
        json={**AccessibilityPreferences().model_dump(), "high_contrast": True},
    )
    assert first.status_code == 200
    version = first.json()["version"]

    stale = client.put(
        "/user-preferences/accessibility",
        headers=headers,
        json={**AccessibilityPreferences().model_dump(), "version": version + 999, "high_contrast": False},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"] == "Request failed."


def test_health_preferences_revoke_removes_ciphertext(client, db, make_lab, make_lab_user):
    lab = make_lab("Revoke Health Lab")
    user = make_lab_user(lab.id, role="admin")
    headers = _headers(user.id, lab.id)

    client.put(
        "/user-preferences/health",
        headers=headers,
        json={
            "preferences": {"other_health_considerations": "private"},
            "consent": True,
            "consent_version": "health-v1",
        },
    )
    revoked = client.delete("/user-preferences/health", headers=headers)

    assert revoked.status_code == 200
    assert revoked.json()["consent_granted"] is False
    row = db.execute(text("SELECT encrypted_payload, consent_granted FROM health_preferences WHERE user_id = :user_id"), {"user_id": user.id}).fetchone()
    assert row == (None, False)
