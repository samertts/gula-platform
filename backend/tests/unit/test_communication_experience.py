"""PROGRAM-COMM-003 tests — User Communication Experience Layer.

Covers: domain rules (categories, priorities, quiet hours, weekend/holiday,
mandatory enforcement, digest deferral, JSON round-trip), preferences
service (sanitization, mute protection), inbox service (durable sink,
filter/search/pagination, actions, history, retry, purge, groups), and the
HTTP API (auth + object-level isolation + protections).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from app._compat import UTC
from app.communication.experience.domain import (
    MANDATORY_CATEGORIES,
    MANDATORY_CHANNELS,
    Frequency,
    InboxState,
    NotificationCategory,
    QuietHoursRules,
    UserPreferences,
    UserPriority,
    category_enabled,
    channel_enabled,
    parse_tz,
    quiet_hours_blocked,
)
from app.communication.experience.gateway import send_communication
from app.communication.experience.inbox_service import (
    bulk_state,
    get_inbox_item,
    grouped_summary,
    history,
    list_inbox,
    purge,
    retry_delivery,
    set_pinned,
    set_state,
    unread_count,
)
from app.communication.experience.preferences_service import (
    channel_catalog,
    get_preferences,
    mute_category,
    mute_channel,
    save_preferences,
    update_preferences,
)
from app.communication.experience.sinks import DurableInAppSink
from app.models.communication_experience import UserNotification
from sqlalchemy.orm import Session, sessionmaker

from shared.communication.model import OutboundMessage

# ── Domain: categories & priorities ───────────────────────────────────────────


def test_category_enum_complete_and_unknown_falls_back():
    assert {c.value for c in NotificationCategory} >= {
        "security", "authentication", "password_reset", "account", "clinical",
        "laboratory", "pharmacy", "hospital", "finance", "billing",
        "appointments", "orders", "reports", "inventory", "administration",
        "system", "monitoring", "emergency", "marketing",
    }
    assert NotificationCategory("bogus") == NotificationCategory.SYSTEM


def test_priority_round_trip():
    assert UserPriority.CRITICAL.to_core().value == "mandatory"
    assert UserPriority.MEDIUM.to_core().value == "normal"
    assert UserPriority.from_core("urgent") == UserPriority.CRITICAL
    assert UserPriority("bogus") == UserPriority.MEDIUM


def test_mandatory_categories_never_disabled():
    assert set(MANDATORY_CATEGORIES) == {"security", "authentication", "password_reset", "emergency"}
    assert "inapp" in MANDATORY_CHANNELS
    assert category_enabled("security", {"security": False}) is True
    assert category_enabled("marketing", {"marketing": False}) is False
    assert channel_enabled("inapp", "security", {"inapp": False}) is True
    assert channel_enabled("email", "laboratory", {"email": False}) is False


def test_emergency_override_enables_everything():
    assert category_enabled("marketing", {"marketing": False}, emergency_override=True) is True


# ── Domain: quiet hours / weekend / holiday ───────────────────────────────────


def _baghdad_utc_time(hour: int) -> datetime:
    # Asia/Baghdad is UTC+3; construct UTC instant whose Baghdad time == hour.
    return datetime(2026, 1, 15, hour - 3, 30, tzinfo=timezone.utc)


def test_quiet_hours_within_window():
    rules = QuietHoursRules(enabled=True, start="22:00", end="06:00")
    blocked, reason = quiet_hours_blocked(
        _baghdad_utc_time(23), "Asia/Baghdad", rules,
        category="laboratory", priority=UserPriority.MEDIUM,
    )
    assert blocked is True and reason == "quiet_hours"


def test_quiet_hours_outside_window_and_disabled():
    rules = QuietHoursRules(enabled=True, start="22:00", end="06:00")
    blocked, _ = quiet_hours_blocked(
        _baghdad_utc_time(14), "Asia/Baghdad", rules,
        category="laboratory", priority=UserPriority.MEDIUM,
    )
    assert blocked is False
    blocked, _ = quiet_hours_blocked(
        _baghdad_utc_time(23), "Asia/Baghdad", QuietHoursRules(enabled=False),
        category="laboratory", priority=UserPriority.MEDIUM,
    )
    assert blocked is False


def test_quiet_hours_invalid_time_and_bad_tz_are_safe():
    rules = QuietHoursRules(enabled=True, start="not-a-time", end="06:00")
    blocked, _ = quiet_hours_blocked(
        _baghdad_utc_time(23), "Asia/Baghdad", rules,
        category="laboratory", priority=UserPriority.MEDIUM,
    )
    assert blocked is False
    blocked, _ = quiet_hours_blocked(
        datetime(2026, 1, 15, 23, 0, tzinfo=timezone.utc), "Not/AZone", rules,
        category="laboratory", priority=UserPriority.MEDIUM,
    )
    assert blocked is False


def test_critical_priority_bypasses_quiet_hours():
    rules = QuietHoursRules(enabled=True, start="22:00", end="06:00")
    blocked, reason = quiet_hours_blocked(
        _baghdad_utc_time(23), "Asia/Baghdad", rules,
        category="laboratory", priority=UserPriority.CRITICAL,
    )
    assert blocked is False and reason == "mandatory"
    blocked, reason = quiet_hours_blocked(
        _baghdad_utc_time(23), "Asia/Baghdad", rules,
        category="security", priority=UserPriority.MEDIUM,
    )
    assert blocked is False and reason == "mandatory"


def test_weekend_rule():
    saturday = datetime(2026, 1, 17, 12, 0, tzinfo=timezone.utc)  # Baghdad Sat
    blocked, reason = quiet_hours_blocked(
        saturday, "Asia/Baghdad", None,
        category="laboratory", priority=UserPriority.MEDIUM,
        weekend_rules=True,
    )
    assert blocked is True and reason == "weekend"
    blocked, _ = quiet_hours_blocked(
        saturday, "Asia/Baghdad", None,
        category="laboratory", priority=UserPriority.MEDIUM,
    )
    assert blocked is False


def test_emergency_override_unblocks():
    blocked, reason = quiet_hours_blocked(
        _baghdad_utc_time(23), "Asia/Baghdad",
        QuietHoursRules(enabled=True, start="22:00", end="06:00"),
        category="laboratory", priority=UserPriority.MEDIUM,
        emergency_override=True,
    )
    assert blocked is False and reason == "emergency_override"


# ── Domain: preferences + decide_delivery ─────────────────────────────────────


def test_defaults_and_json_round_trip():
    prefs = UserPreferences.defaults(42)
    assert prefs.locale == "ar"
    assert prefs.timezone == "Asia/Baghdad"
    assert prefs.frequency == Frequency.IMMEDIATE
    restored = UserPreferences.from_json(42, prefs.to_json())
    assert restored.to_dict() == prefs.to_dict()
    assert UserPreferences.from_json(1, None) == UserPreferences.defaults(1)
    assert UserPreferences.from_json(1, "{not json").channels == UserPreferences.defaults(1).channels


def test_decide_delivery_respects_mutes_and_order():
    prefs = UserPreferences.defaults(1)
    prefs.channels["email"] = False
    prefs.channel_priority = ["inapp", "email", "sms"]
    channels, skipped = prefs.decide_delivery(
        category="laboratory", priority=UserPriority.MEDIUM,
    )
    assert channels == ["inapp", "sms"]
    assert skipped == []


def test_decide_delivery_blocks_non_critical_in_quiet_hours():
    prefs = UserPreferences.defaults(1)
    prefs.quiet_hours = QuietHoursRules(enabled=True, start="22:00", end="06:00")
    channels, skipped = prefs.decide_delivery(
        category="laboratory", priority=UserPriority.MEDIUM,
        now=_baghdad_utc_time(23),
    )
    assert channels == ["inapp"]
    assert ("email", "quiet_hours") in skipped


def test_decide_delivery_keeps_mandatory_during_quiet_hours():
    prefs = UserPreferences.defaults(1)
    prefs.quiet_hours = QuietHoursRules(enabled=True, start="22:00", end="06:00")
    channels, _ = prefs.decide_delivery(
        category="security", priority=UserPriority.HIGH,
        now=_baghdad_utc_time(23),
    )
    assert "inapp" in channels and "email" in channels


# ── Sinks: durable inbox writer ────────────────────────────────────────────────


def _sink_factory(db: Session):
    factory = sessionmaker(bind=db.get_bind(), autoflush=False)
    return DurableInAppSink(session_factory=factory)


def _message(**overrides) -> OutboundMessage:
    base = {
        "content": "العملية تمت بنجاح",
        "subject": "Order ready",
        "locale": "ar",
        "template_id": "inform.order_validated",
        "metadata": {"context": {"user_id": 7, "category": "laboratory", "priority": "medium"}},
    }
    base.update(overrides)
    return OutboundMessage(**base)


def test_durable_sink_creates_inbox_row_with_history(db):
    sink = _sink_factory(db)
    sink.record("inapp-abc", "user:7", _message())
    rows = db.query(UserNotification).filter(UserNotification.user_id == 7).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.state == "unread"
    assert row.category == "laboratory"
    assert row.priority == "medium"
    assert row.delivery_id == "inapp-abc"
    assert "تمت" in row.body
    assert row.title == "Order ready"
    events = history(db, 7, row.id)
    assert events[0]["event_type"] == "delivered"
    assert events[0]["channel"] == "inapp"


def test_durable_sink_prefers_gateway_delivery_id(db):
    sink = _sink_factory(db)
    sink.record("inapp-abc", "user:7", _message(metadata={"context": {"user_id": 7, "delivery_id": "gateway-1"}}))
    row = db.query(UserNotification).filter(UserNotification.user_id == 7).first()
    assert row.delivery_id == "gateway-1"


def test_durable_sink_skips_without_user_id(db):
    sink = _sink_factory(db)
    sink.record("inapp-x", "someone@example.com", _message(metadata={"context": {}}))
    assert db.query(UserNotification).count() == 0


# ── Inbox service: querying ───────────────────────────────────────────────────


@pytest.fixture
def inbox(db):
    sink = _sink_factory(db)
    sink.record("d-1", "user:7", _message(subject="Critical result", metadata={"context": {"user_id": 7, "category": "clinical", "priority": "high"}}))
    sink.record("d-2", "user:7", _message(subject="Order validated", metadata={"context": {"user_id": 7, "category": "orders", "priority": "medium", "group_key": "orders"}}))
    sink.record("d-3", "user:7", _message(subject="Backup failed", metadata={"context": {"user_id": 7, "category": "system", "priority": "high", "group_key": "ops"}}))
    sink.record("d-4", "user:7", _message(subject="Marketing", metadata={"context": {"user_id": 7, "category": "marketing", "priority": "low"}}))
    sink.record("d-5", "user:8", _message(subject="Other user", metadata={"context": {"user_id": 8, "category": "system"}}))
    return db


def test_list_inbox_pagination_and_filters(inbox):
    first = list_inbox(inbox, 7, limit=2)
    assert len(first["items"]) == 2
    assert first["next_cursor"] is not None
    assert first["total"] == 4
    second = list_inbox(inbox, 7, limit=2, cursor=first["next_cursor"])
    assert len(second["items"]) == 2
    assert second["next_cursor"] is None  # only 4 items → exactly 2 pages
    seen = {i["id"] for i in first["items"] + second["items"]}
    assert len(seen) == 4  # pages are disjoint and cover the whole inbox


def test_list_inbox_category_and_priority_filters(inbox):
    items = list_inbox(inbox, 7, category="system")["items"]
    assert len(items) == 1 and items[0]["title"] == "Backup failed"
    items = list_inbox(inbox, 7, priority="high")["items"]
    assert len(items) == 2
    items = list_inbox(inbox, 7, state="unread")["items"]
    assert len(items) == 4


def test_list_inbox_search(inbox):
    items = list_inbox(inbox, 7, search="critical")["items"]
    assert len(items) == 1 and items[0]["category"] == "clinical"
    items = list_inbox(inbox, 7, search="غير موجود")["items"]
    assert items == []


def test_list_inbox_group_and_pinned(inbox):
    items = list_inbox(inbox, 7, group_key="orders")["items"]
    assert len(items) == 1
    assert list_inbox(inbox, 7, pinned=True)["items"] == []
    groups = grouped_summary(inbox, 7)
    by_key = {g["group_key"]: g["count"] for g in groups}
    assert by_key == {"orders": 1, "ops": 1}


def test_unread_count_and_user_isolation(inbox):
    assert unread_count(inbox, 7) == 4
    assert unread_count(inbox, 8) == 1
    items = list_inbox(inbox, 7)["items"]
    assert all(i["user_id"] == 7 for i in items)


# ── Inbox service: actions & history ──────────────────────────────────────────


def test_state_actions_append_history(inbox):
    row = get_inbox_item(inbox, 7, 1)
    assert row.state == InboxState.UNREAD.value
    set_state(inbox, 7, 1, "read")
    assert get_inbox_item(inbox, 7, 1).state == "read"
    set_state(inbox, 7, 1, "unread")
    assert get_inbox_item(inbox, 7, 1).state == "unread"
    set_state(inbox, 7, 1, "archive")
    assert get_inbox_item(inbox, 7, 1).state == "archived"
    set_state(inbox, 7, 1, "restore")
    assert get_inbox_item(inbox, 7, 1).state == "read"
    events = history(inbox, 7, 1)
    kinds = [e["event_type"] for e in events]
    # Most-recent-first: the 4 transitions plus the initial durable delivery.
    assert kinds == ["state_restored", "state_archived", "state_unread", "state_read", "delivered"]


def test_delete_hides_but_purge_removes(inbox):
    set_state(inbox, 7, 1, "delete")
    assert list_inbox(inbox, 7)["total"] == 3
    assert list_inbox(inbox, 7, include_deleted=True)["total"] == 4
    assert get_inbox_item(inbox, 7, 1).state == "deleted"
    purge(inbox, 7, 1)
    with pytest.raises(LookupError):
        get_inbox_item(inbox, 7, 1)


def test_bulk_state_and_pin(inbox):
    assert bulk_state(inbox, 7, "read")["updated"] == 4
    assert unread_count(inbox, 7) == 0
    set_pinned(inbox, 7, 2, True)
    items = list_inbox(inbox, 7)["items"]
    assert items[0]["id"] == 2 and items[0]["pinned"] is True
    events = history(inbox, 7, 2)
    assert events[0]["event_type"] == "pinned"


def test_retry_delivery_records_outcome(inbox):
    def good(_ctx):
        return {"success": True}
    result = retry_delivery(inbox, 7, 1, good)
    assert result["success"] is True
    assert history(inbox, 7, 1)[0]["event_type"] == "retried"

    def bad(_ctx):
        return {"success": False, "error": "provider down"}
    result = retry_delivery(inbox, 7, 1, bad)
    assert result["success"] is False and result["error"] == "provider down"
    assert history(inbox, 7, 1)[0]["event_type"] == "error"


def test_retry_requires_ownership(inbox):
    with pytest.raises(LookupError):
        retry_delivery(inbox, 8, 1, lambda _c: {"success": True})


# ── Preferences service ───────────────────────────────────────────────────────


def test_preferences_crud_and_sanitization(db):
    prefs = update_preferences(
        db, 7,
        {
            "locale": "en",
            "timezone": "Asia/Baghdad",
            "channels": {"email": False, "inapp": False},
            "categories": {"marketing": False, "security": False},
            "frequency": "digest",
            "quiet_hours": {"enabled": True, "start": "21:00", "end": "07:00"},
        },
    )
    assert prefs.locale == "en"
    assert prefs.channels["email"] is False
    assert prefs.channels["inapp"] is True  # mandatory — never disabled
    assert prefs.categories["marketing"] is False
    assert prefs.categories["security"] is True  # mandatory — never disabled
    assert prefs.frequency == Frequency.DIGEST
    assert prefs.quiet_hours.enabled is True
    reloaded = get_preferences(db, 7)
    assert reloaded.to_dict() == prefs.to_dict()


def test_mute_protection(db):
    with pytest.raises(ValueError):
        mute_category(db, 7, "security")
    with pytest.raises(ValueError):
        mute_channel(db, 7, "inapp")
    prefs = mute_category(db, 7, "marketing", muted=True)
    assert prefs.categories["marketing"] is False
    prefs = mute_channel(db, 7, "email", muted=True)
    assert prefs.channels["email"] is False


def test_channel_catalog():
    catalog = channel_catalog(provider_channels=["inapp", "email"])
    by_id = {c["id"]: c for c in catalog}
    assert by_id["inapp"]["mandatory"] is True
    assert by_id["inapp"]["status"] == "ready"
    assert by_id["email"]["available"] is True
    assert "discord" in by_id


def test_save_preferences_sets_timestamp(db):
    prefs = save_preferences(db, 9, UserPreferences.defaults(9))
    assert prefs.updated_at
    assert get_preferences(db, 9).updated_at


# ── Gateway ───────────────────────────────────────────────────────────────────


def test_gateway_suppressed_when_no_channels(db, monkeypatch):
    prefs = get_preferences(db, 7)
    prefs.channels = dict.fromkeys(prefs.channels, False)
    prefs.channel_priority = []
    save_preferences(db, 7, prefs)
    monkeypatch.setattr("app.communication.experience.gateway.get_preferences", lambda d, uid: prefs)
    result = send_communication(
        db, 7, category="laboratory", priority="medium",
        title="x", body="y",
    )
    assert result["delivered"] is False
    assert result["reason"] == "no_channels"


def test_gateway_digest_defers_external_channels(db, monkeypatch):
    prefs = get_preferences(db, 7)
    prefs.frequency = Frequency.DIGEST
    save_preferences(db, 7, prefs)

    class FakeCenter:
        def dispatch(self, *a, **kw):
            return type("R", (), {"state": "delivered", "error": None})()

    import app.communication
    import app.communication.experience.gateway as gateway_mod

    monkeypatch.setattr(app.communication, "get_communication_center", lambda: FakeCenter())
    result = send_communication(
        db, 7, category="laboratory", priority="medium",
        title="digest test", body="b",
    )
    assert result["channels"] == ["inapp"]
    assert any(reason == "digest_pending" for _, reason in result["skipped"])


def test_gateway_digest_never_defers_critical(db, monkeypatch):
    prefs = get_preferences(db, 7)
    prefs.frequency = Frequency.DIGEST
    save_preferences(db, 7, prefs)

    class FakeCenter:
        def dispatch(self, *a, **kw):
            return type("R", (), {"state": "delivered", "error": None})()

    import app.communication
    import app.communication.experience.gateway as gateway_mod

    monkeypatch.setattr(app.communication, "get_communication_center", lambda: FakeCenter())
    result = send_communication(
        db, 7, category="security", priority="critical",
        title="alert", body="b",
    )
    assert "inapp" in result["channels"]
    assert all(reason != "digest_pending" for _, reason in result["skipped"])


# ── HTTP API (auth + object-level isolation + protections) ────────────────────


@pytest.fixture
def comm_api_users(db, make_lab):
    """Persist users id=7 and id=8 (matching the inbox fixture) so the HTTP
    auth dependency (get_current_user) can resolve the bearer tokens."""
    from app.models.lab_user import LabUser
    from app.security.auth import hash_password

    lab = make_lab(name="Communication Lab")
    for uid, name in ((7, "Comm User Seven"), (8, "Comm User Eight")):
        db.add(
            LabUser(
                id=uid,
                lab_id=lab.id,
                name=name,
                email=f"comm{uid}@test.com",
                password_hash=hash_password("Testpass1"),
                role="admin",
                is_active=True,
            )
        )
    db.commit()
    return lab


def _headers(user_id: int, lab_id: int = 1) -> dict:
    from app.security.auth import create_token

    return {"Authorization": f"Bearer {create_token({'user_id': user_id, 'lab_id': lab_id, 'role': 'admin'})}"}


def test_api_preferences_catalog(client, comm_api_users):
    resp = client.get("/communication/preferences/catalog", headers=_headers(7))
    assert resp.status_code == 200
    body = resp.json()
    channels = {c["id"] for c in body["channels"]}
    assert "inapp" in channels and "email" in channels
    assert "security" in body["mandatory_categories"]


def test_api_preferences_roundtrip(client, comm_api_users):
    resp = client.put(
        "/communication/preferences",
        json={"timezone": "Asia/Baghdad", "channels": {"email": False}},
        headers=_headers(7),
    )
    assert resp.status_code == 200
    assert resp.json()["channels"]["email"] is False
    assert resp.json()["channels"]["inapp"] is True
    resp = client.get("/communication/preferences", headers=_headers(7))
    assert resp.json()["timezone"] == "Asia/Baghdad"


def test_api_cannot_mute_mandatory(client, comm_api_users):
    resp = client.post(
        "/communication/preferences/mute-category?category=security",
        json={"muted": True},
        headers=_headers(7),
    )
    assert resp.status_code == 400
    resp = client.post(
        "/communication/preferences/mute-channel?channel=inapp",
        json={"muted": True},
        headers=_headers(7),
    )
    assert resp.status_code == 400


def test_api_inbox_actions_and_ownership(client, inbox, comm_api_users):
    resp = client.patch("/communication/inbox/1?action=read", headers=_headers(7))
    assert resp.status_code == 200
    assert resp.json()["state"] == "read"
    resp = client.get("/communication/inbox/unread-count", headers=_headers(7))
    assert resp.json()["unread"] == 3
    resp = client.patch("/communication/inbox/5?action=read", headers=_headers(7))
    assert resp.status_code == 404  # user 8's notification
    resp = client.get("/communication/inbox/5", headers=_headers(7))
    assert resp.status_code == 404
    resp = client.get("/communication/inbox?category=system&limit=1", headers=_headers(7))
    body = resp.json()
    assert len(body["items"]) == 1 and body["total"] >= 1


def test_api_inbox_detail_has_history(client, inbox, comm_api_users):
    resp = client.get("/communication/inbox/1", headers=_headers(7))
    assert resp.status_code == 200
    body = resp.json()
    assert body["item"]["id"] == 1
    assert body["history"][0]["event_type"] == "delivered"


def test_api_requires_auth(client):
    assert client.get("/communication/inbox").status_code == 401
    assert client.get("/communication/preferences").status_code == 401
