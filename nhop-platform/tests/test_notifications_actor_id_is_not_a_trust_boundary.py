"""P0 characterization test — final cross-cutting forensic pass.

notifications.py has NO role gate at all (unlike citizens.py/test_results.py,
which at least require an X-Role value post-batch-2). Every route trusts
X-Actor-Id as a fully authenticated user_id with zero verification, and uses
it directly as the row-scoping key (services/notification.py filters
`Notification.recipient_id == user_id`). The SQL-level scoping is correct;
the identity feeding it is not authenticated at all.

Impact is not hypothetical: test_results.py's _fire_critical_alert() sends
citizens their own critical-result notifications with
`recipient_id=citizen.health_id` — i.e. a citizen's health_id (a
non-secret, discoverable identifier: it's what citizens.py's own /search
and /{health_id} endpoints return) IS a valid X-Actor-Id for reading that
citizen's critical lab alerts. No password, token, or session — just
knowing (or guessing, or having searched for) someone's health_id.

This is the exact defect class flagged in the corrected security-review
guidance: "user_id/account_id ... taken from request data instead of
trusted session context." It shares X-Role's root cause (no real identity
stack in nhop-platform yet) and shares its fix location and blocker (see
docs/engineering/MUSTAFA_PARALLEL_WORK_MAP.md finding #11) — not
re-designed or fixed here, only proven and documented, per this pass's
explicit no-speculative-implementation, no-competing-auth-implementation
instructions.
"""
from __future__ import annotations


def test_any_caller_reads_another_users_notifications_by_declaring_their_id(app_client):
    client, Session = app_client
    from app.services.notification import send_notification
    from app.models.notification import NotificationType, NotificationPriority

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

    # No login, no token, no session — just a claimed identity.
    resp = client.get("/v1/notifications/", headers={"X-Actor-Id": "HID-VICTIM"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert "حرجة" in body["items"][0]["title"]
    assert "6.2" in body["items"][0]["body"]

    # A different claimed identity sees nothing — proving the isolation is
    # real at the SQL layer, and therefore that the *only* thing standing
    # between an attacker and this data is an unverified string they typed.
    other = client.get("/v1/notifications/", headers={"X-Actor-Id": "HID-SOMEONE-ELSE"})
    assert other.status_code == 200
    assert other.json()["total"] == 0


def test_any_caller_can_mark_another_users_critical_alert_as_read(app_client):
    """Tampering, not just reading: an attacker who guesses/knows a
    victim's id can also silently suppress their critical-result alert by
    marking it read before the real recipient ever sees it."""
    client, Session = app_client
    from app.services.notification import send_notification
    from app.models.notification import NotificationType, NotificationPriority

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
        notification_id = str(row.id)

    resp = client.put(
        f"/v1/notifications/{notification_id}/read",
        headers={"X-Actor-Id": "HID-VICTIM-2"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


def test_missing_x_actor_id_is_the_only_thing_actually_enforced(app_client):
    """Confirms the finding isn't "no gate at all, anything goes" — there
    IS a check. It just isn't authentication."""
    client, _ = app_client
    resp = client.get("/v1/notifications/")
    assert resp.status_code == 401
