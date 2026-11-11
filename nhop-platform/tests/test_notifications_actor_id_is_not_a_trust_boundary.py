"""F1 (notifications) closure proof.

notifications.py used to trust X-Actor-Id as a fully authenticated user_id
with zero verification, and used it directly as the row-scoping key
(services/notification.py filters `Notification.recipient_id == user_id`).
The SQL-level scoping was correct; the identity feeding it was not
authenticated at all — a citizen's health_id (non-secret, returned by
citizens.py's own /search and /{health_id} endpoints) was a valid
X-Actor-Id for reading, and silencing, that citizen's own critical-result
alerts.

Identity now comes exclusively from app.core.trusted_context, which fails
closed (503) until a real identity provider is federated. These tests prove
that against the production dependency directly — bypassing conftest's
legacy-header compatibility shim on purpose, the same way
test_rbac_is_not_a_trust_boundary.py does, since honoring X-Actor-Id there
would reproduce exactly the vulnerability this file used to demonstrate.
"""
from __future__ import annotations


def _drop_identity_shim(client):
    """See test_rbac_is_not_a_trust_boundary.py's copy of this helper for why
    the import happens here rather than at module level."""
    from app.core.trusted_context import require_trusted_context

    client.app.dependency_overrides.pop(require_trusted_context, None)


def test_claiming_a_victims_id_no_longer_reads_their_notifications(app_client):
    client, Session = app_client
    from app.models.notification import NotificationPriority, NotificationType
    from app.services.notification import send_notification

    with Session() as s:
        send_notification(
            s,
            recipient_id="HID-VICTIM",
            recipient_role="citizen",
            type=NotificationType.critical_result,
            title="نتيجة حرجة: الهيموغلوبين",
            body="تحليل HGB | القيمة: 6.2 g/dL | الاتجاه: down",
            priority=NotificationPriority.urgent,
        )
        s.commit()

    _drop_identity_shim(client)

    resp = client.get("/v1/notifications/", headers={"X-Actor-Id": "HID-VICTIM"})
    assert resp.status_code == 503


def test_claiming_a_victims_id_no_longer_suppresses_their_alert(app_client):
    """Tampering, not just reading: this used to let an attacker who
    guessed/knew a victim's id silently mark their critical alert as read."""
    client, Session = app_client
    from app.models.notification import NotificationPriority, NotificationType
    from app.services.notification import send_notification

    with Session() as s:
        row = send_notification(
            s,
            recipient_id="HID-VICTIM-2",
            recipient_role="citizen",
            type=NotificationType.critical_result,
            title="نتيجة حرجة",
            body="...",
            priority=NotificationPriority.urgent,
        )
        s.commit()
        notification_uuid = row.id
        notification_id = str(row.id)
        was_read_before = row.is_read

    _drop_identity_shim(client)

    resp = client.put(
        f"/v1/notifications/{notification_id}/read",
        headers={"X-Actor-Id": "HID-VICTIM-2"},
    )
    assert resp.status_code == 503

    with Session() as s:
        from app.models.notification import Notification

        fresh = s.query(Notification).filter(Notification.id == notification_uuid).first()
        assert fresh.is_read == was_read_before  # unchanged: denied before mutation


def test_missing_and_forged_x_actor_id_fail_identically(app_client):
    """Before the fix, "missing header" (401) and "forged header" (200) were
    distinguishable — that distinguishability is what made the header
    guessable/attackable in the first place. Both must now 503 alike."""
    client, _ = app_client
    _drop_identity_shim(client)

    missing = client.get("/v1/notifications/")
    forged = client.get("/v1/notifications/", headers={"X-Actor-Id": "HID-ANYONE"})

    assert missing.status_code == 503
    assert forged.status_code == 503
