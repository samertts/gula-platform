"""Enterprise Telegram provider tests (PROGRAM-COMM-002A).

Covers the enterprise capabilities layered on top of the existing provider:

  * keyboard builders (inline, reply, force-reply, remove)
  * media groups (album), MIME detection, attachment helpers
  * groups / super-groups / topics / channels via chat_id
  * rich messages (reply_to, message_thread_id, reply_markup)
  * edit / delete messages
  * webhooks (set/delete/getWebhookInfo/getMe) + secret validation
  * polling (getUpdates), auto mode switching
  * broadcast / batch with pacing + dedupe
  * scheduled delivery via the TaskWorker handler
  * security guards: replay, flood, rate limiting, redaction
  * Prometheus-style metrics exposition

These are computed — the Bot API is patched at the httpx.Client.post boundary.
"""

from __future__ import annotations

import json as _json_module
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import httpx
import pytest

from shared.notifications.telegram import (
    TelegramNetworkSpeed,
    TelegramNotificationService,
    TelegramWebhookInfo,
    append_prometheus_metrics,
    build_force_reply,
    build_inline_keyboard,
    build_remove_keyboard,
    build_reply_keyboard,
    detect_mime_type,
    redact_secrets,
    validate_webhook_secret,
)

FAKE_TOKEN = "142536" + ":" + "A" * 40
POST = "httpx.Client.post"


def _client(**kwargs):
    defaults = {
        "bot_token": FAKE_TOKEN,
        "timeout_seconds": 12,
        "max_retries": 2,
    }
    defaults.update(kwargs)
    return TelegramNotificationService(**defaults)


def _resp(payload, status_code=200):
    request = httpx.Request("POST", "https://api.telegram.org")
    return httpx.Response(status_code, json=payload, request=request)


def _ok_response(message_id=42):
    return _resp({"ok": True, "result": {"message_id": message_id}})


def _ok(result):
    return _resp({"ok": True, "result": result})


def _err(description="bad request", error_code=400):
    return _resp({"ok": False, "description": description, "error_code": error_code})


# ── Keyboard builders ─────────────────────────────────────────────────────────


class TestKeyboardBuilders:
    def test_inline_keyboard_valid(self):
        kb = build_inline_keyboard([[{"text": "Yes", "callback_data": "y"}]])
        assert kb == {"inline_keyboard": [[{"text": "Yes", "callback_data": "y"}]]}

    def test_inline_keyboard_multiple_rows(self):
        kb = build_inline_keyboard([[{"text": "1"}, {"text": "2"}], [{"text": "3"}]])
        assert len(kb["inline_keyboard"]) == 2

    def test_inline_keyboard_empty_rejected(self):
        with pytest.raises(ValueError):
            build_inline_keyboard([])

    def test_inline_keyboard_over_100_rejected(self):
        rows = [[{"text": str(i)}] for i in range(101)]
        with pytest.raises(ValueError):
            build_inline_keyboard(rows)

    def test_inline_keyboard_bad_row_rejected(self):
        with pytest.raises(ValueError):
            build_inline_keyboard([[]])
        with pytest.raises(ValueError):
            build_inline_keyboard([[{"callback_data": "no-text"}]])

    def test_reply_keyboard(self):
        kb = build_reply_keyboard([["A", "B"], ["C"]])
        assert kb["keyboard"][0] == [{"text": "A"}, {"text": "B"}]
        assert kb["resize_keyboard"] is True

    def test_reply_keyboard_empty_rejected(self):
        with pytest.raises(ValueError):
            build_reply_keyboard([])
        with pytest.raises(ValueError):
            build_reply_keyboard([[]])

    def test_remove_keyboard(self):
        assert build_remove_keyboard() == {"remove_keyboard": True, "selective": False}

    def test_force_reply(self):
        assert build_force_reply() == {"force_reply": True, "selective": False}


# ── MIME detection ────────────────────────────────────────────────────────────


class TestMimeDetection:
    def test_pdf(self):
        assert detect_mime_type("report.pdf") == "application/pdf"

    def test_csv(self):
        assert detect_mime_type("data.csv") == "text/csv"

    def test_xlsx(self):
        assert (
            detect_mime_type("r.xlsx")
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_docx(self):
        assert (
            detect_mime_type("l.docx")
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def test_zip(self):
        assert detect_mime_type("a.zip") == "application/zip"

    def test_audio_video(self):
        assert detect_mime_type("s.mp3") == "audio/mpeg"
        assert detect_mime_type("c.mp4") == "video/mp4"

    def test_unknown_fallback(self):
        assert detect_mime_type("f.xyz") == "application/octet-stream"
        assert detect_mime_type("noext") == "application/octet-stream"


# ── Rich messages ────────────────────────────────────────────────────────────


class TestRichMessages:
    def test_reply_markup_and_reply_to(self):
        service = _client()
        captured = {}
        kb = {"inline_keyboard": [[{"text": "Go", "url": "http://example.com"}]]}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.send_text(
                "123", "Hello", reply_markup=kb, reply_to_message_id=9,
            )
        assert result.success
        assert _json_module.loads(captured["json"]["reply_markup"]) == kb
        assert captured["json"]["reply_to_message_id"] == 9

    def test_message_thread_id_for_topic(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.send_to_thread(-100123, 44, "topic msg")
        assert result.success
        assert captured["json"]["message_thread_id"] == 44

    def test_reply(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.reply(123, "replying", 55)
        assert result.success
        assert captured["json"]["reply_to_message_id"] == 55

    def test_edit_message(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.edit_message(123, 77, "updated")
        assert result.success
        assert captured["json"]["message_id"] == 77

    def test_edit_message_html_parse_mode(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.edit_message(123, 77, "<b>x</b>", "HTML")
        assert captured["json"]["parse_mode"] == "HTML"

    def test_delete_message(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.delete_message(123, 88)
        assert result.success
        assert captured["json"]["message_id"] == 88


# ── Media ─────────────────────────────────────────────────────────────────────


class TestMedia:
    def test_media_group_file_ids(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _resp({"ok": True, "result": [{"message_id": 1}, {"message_id": 2}]})

        media = [
            {"type": "photo", "media": "fileAAAA", "caption": "one"},
            {"type": "photo", "media": "fileBBBB"},
        ]
        with patch(POST, new=fake_post):
            result = service.send_media_group(123, media)
        assert result.success
        assert result.message_id == 1
        assert len(_json_module.loads(captured["json"]["media"])) == 2

    def test_media_group_bytes_upload(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["files"] = files
            captured["media"] = _json_module.loads(data["media"])
            return _ok_response(3)

        media = [
            {"type": "photo", "media": b"\x89PNGdata", "filename": "a.png", "mime_type": "image/png"},
        ]
        with patch(POST, new=fake_post):
            result = service.send_media_group(123, media)
        assert result.success
        assert "m0" in captured["files"]
        assert captured["media"][0]["media"] == "attach://m0"

    def test_media_group_too_many(self):
        media = [{"type": "photo", "media": "f"}] * 11
        result = _client().send_media_group(123, media)
        assert not result.success
        assert "1 and 10" in (result.error or "")

    def test_media_group_missing_fields(self):
        result = _client().send_media_group(123, [{"type": "photo"}])
        assert not result.success

    def test_send_attachment_auto_mime(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["files"] = files
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.send_attachment(123, b"pdf", filename="doc.pdf")
        assert result.success
        assert captured["files"]["document"][2] == "application/pdf"

    def test_audio_video_voice_animation_use_document(self):
        service = _client()
        methods = []

        def fake_post(client, url, *, json=None, data=None, files=None):
            methods.append(url.rsplit("/", 1)[-1])
            return _ok_response()

        with patch(POST, new=fake_post):
            service.send_audio(123, "a.mp3", filename="a.mp3")
            service.send_video(123, "v.mp4", filename="v.mp4")
            service.send_voice(123, "v.ogg", filename="v.ogg")
            service.send_animation(123, "g.gif", filename="g.gif")
        assert all(m == "sendDocument" for m in methods)

    def test_send_location(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.send_location(123, 33.3, 44.4)
        assert result.success
        assert captured["json"]["latitude"] == 33.3
        assert captured["json"]["longitude"] == 44.4

    def test_send_contact(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.send_contact(123, "+964", "Samer")
        assert result.success
        assert captured["json"]["phone_number"] == "+964"


# ── Groups / channels ────────────────────────────────────────────────────────


class TestGroupsChannels:
    def test_negative_group_chat_id(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.send_text(-100123456, "group message")
        assert result.success
        assert captured["json"]["chat_id"] == -100123456

    def test_channel_username(self):
        service = _client()
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok_response()

        with patch(POST, new=fake_post):
            result = service.send_text("@gula_announcements", "channel broadcast")
        assert result.success
        assert captured["json"]["chat_id"] == "@gula_announcements"

    def test_get_chat(self):
        def fake_post(client, url, *, json=None, data=None, files=None):
            return _ok({"id": -100, "type": "supergroup", "title": "Lab Ops"})

        with patch(POST, new=fake_post):
            result = _client().get_chat(-100)
        assert result.ok
        assert result.data["type"] == "supergroup"

    def test_get_chat_members_count(self):
        def fake_post(client, url, *, json=None, data=None, files=None):
            return _ok({"id": -100, "members": 42})

        with patch(POST, new=fake_post):
            result = _client().get_chat_members_count(-100)
        assert result.ok


# ── Webhooks ──────────────────────────────────────────────────────────────────


class TestWebhooks:
    def test_set_webhook(self):
        service = _client(webhook_secret_token="abc123")
        captured = {}

        def fake_post(client, url, *, json=None, data=None, files=None):
            captured["json"] = json
            return _ok(True)

        with patch(POST, new=fake_post):
            result = service.set_webhook(
                "https://gula-platform.org/webhooks/telegram/update",
                secret_token="abc123",
            )
        assert result.ok
        assert captured["json"]["url"].endswith("/webhooks/telegram/update")
        assert captured["json"]["secret_token"] == "abc123"

    def test_delete_webhook(self):
        def fake_post(client, url, *, json=None, data=None, files=None):
            return _ok(True)

        with patch(POST, new=fake_post):
            result = _client().delete_webhook()
        assert result.ok

    def test_get_webhook_info(self):
        def fake_post(client, url, *, json=None, data=None, files=None):
            return _ok(
                {
                    "url": "https://example.com/w",
                    "pending_update_count": 3,
                    "last_error_message": "",
                    "max_connections": 40,
                }
            )

        with patch(POST, new=fake_post):
            info = _client().get_webhook_info()
        assert isinstance(info, TelegramWebhookInfo)
        assert info.is_webhook_set is True
        assert info.pending_update_count == 3

    def test_get_webhook_info_empty(self):
        def fake_post(client, url, *, json=None, data=None, files=None):
            return _ok({"url": "", "pending_update_count": 0, "max_connections": 40})

        with patch(POST, new=fake_post):
            info = _client().get_webhook_info()
        assert info.is_webhook_set is False

    def test_get_me(self):
        def fake_post(client, url, *, json=None, data=None, files=None):
            return _ok({"id": 123, "username": "gula_bot"})

        with patch(POST, new=fake_post):
            result = _client().get_me()
        assert result.ok
        assert result.data["username"] == "gula_bot"

    def test_switch_to_webhook(self):
        service = _client(webhook_secret_token="s")
        calls = []

        def fake_post(client, url, *, json=None, data=None, files=None):
            calls.append(json)
            return _ok(True)

        with patch(POST, new=fake_post):
            service.switch_mode("https://example.com/w")
        assert calls[0]["url"] == "https://example.com/w"
        assert calls[0]["secret_token"] == "s"

    def test_switch_to_polling(self):
        calls = []

        def fake_post(client, url, *, json=None, data=None, files=None):
            calls.append(url)
            return _ok(True)

        with patch(POST, new=fake_post):
            _client().switch_mode("")
        assert "deleteWebhook" in calls[-1]


# ── Secret validation ─────────────────────────────────────────────────────────


class TestWebhookSecret:
    def test_no_configured_secret(self):
        assert validate_webhook_secret("", "") is True
        assert validate_webhook_secret("", "anything") is True

    def test_mismatch_fails(self):
        assert validate_webhook_secret("abc", "def") is False

    def test_missing_header_fails(self):
        assert validate_webhook_secret("abc", "") is False

    def test_match(self):
        assert validate_webhook_secret("abc-123", "abc-123") is True

    def test_service_without_secret(self):
        service = _client()
        assert service.webhook_secret_token == ""


# ── Broadcast / batch ─────────────────────────────────────────────────────────


class TestBroadcastBatch:
    def test_broadcast_dedup_and_pacing(self):
        service = _client()
        sent = []

        def fake_post(client, url, *, json=None, data=None, files=None):
            sent.append(json["chat_id"])
            return _ok_response()

        with patch(POST, new=fake_post):
            results = service.send_broadcast(
                [1, 1, 2, 3], "hi", interval_seconds=0.0,
            )
        assert len(results) == 4
        assert results[1].error == "duplicate recipient skipped"
        assert sent == [1, 2, 3]

    def test_broadcast_rate_limit(self):
        service = _client(max_per_minute=2)
        calls = []

        def fake_post(client, url, *, json=None, data=None, files=None):
            calls.append(json["chat_id"])
            return _ok_response()

        with patch(POST, new=fake_post):
            results = service.send_broadcast([1, 2, 3], "hi", interval_seconds=0.0)
        assert len(calls) <= 2
        assert any(r.error == "rate limit exceeded" for r in results)

    def test_batch_validity(self):
        service = _client()
        with patch(POST, new=lambda client, url, *, json=None, data=None, files=None: _ok_response()):
            results = service.send_batch(
                [
                    {"chat_id": 1, "text": "a"},
                    {"chat_id": 2, "text": "b", "parse_mode": "HTML"},
                    {"chat_id": 3},
                    {"text": "c"},
                ],
                interval_seconds=0.0,
            )
        assert results[0].success is True
        assert results[1].success is True
        assert results[2].error == "batch entry needs chat_id+text"
        assert results[3].error == "batch entry needs chat_id+text"


class TestScheduling:
    @pytest.mark.asyncio
    async def test_schedule_enqueues(self, monkeypatch):
        from app.notifications.telegram_enterprise import EnterpriseTelegramService
        from app.tasks.queue import task_queue

        captured = {}

        async def fake_enqueue(task):
            captured["task"] = task

        monkeypatch.setattr(task_queue, "enqueue", fake_enqueue)
        svc = EnterpriseTelegramService()
        await svc.schedule(123, "hello", delay_seconds=30)
        task = captured["task"]
        assert task.type == "telegram.deliver"
        assert task.payload["chat_id"] == 123
        assert task.payload["delay_seconds"] == 30

    @pytest.mark.asyncio
    async def test_schedule_requires_time(self):
        from app.notifications.telegram_enterprise import EnterpriseTelegramService

        svc = EnterpriseTelegramService()
        with pytest.raises(ValueError):
            await svc.schedule(123, "hi")

    @pytest.mark.asyncio
    async def test_schedule_absolute_time(self, monkeypatch):
        from app.notifications.telegram_enterprise import EnterpriseTelegramService
        from app.tasks.queue import task_queue

        captured = {}

        async def fake_enqueue(task):
            captured["task"] = task

        monkeypatch.setattr(task_queue, "enqueue", fake_enqueue)
        svc = EnterpriseTelegramService()
        await svc.schedule(
            123, "hi", deliver_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        delay = captured["task"].payload["delay_seconds"]
        assert 1798 <= delay <= 1800

    @pytest.mark.asyncio
    async def test_schedule_broadcast(self, monkeypatch):
        from app.notifications.telegram_enterprise import EnterpriseTelegramService
        from app.tasks.queue import task_queue

        captured = {}

        async def fake_enqueue(task):
            captured["task"] = task

        monkeypatch.setattr(task_queue, "enqueue", fake_enqueue)
        svc = EnterpriseTelegramService()
        await svc.schedule_broadcast([1, 2], "broadcast", delay_seconds=5)
        assert captured["task"].payload["chat_id"] == "__broadcast__"
        assert captured["task"].payload["options"]["broadcast_chat_ids"] == [1, 2]

    def test_delivery_summary(self):
        from app.notifications.telegram_enterprise import EnterpriseTelegramService

        from shared.notifications.telegram import TelegramSendResult

        results = [
            TelegramSendResult(True, message_id=5),
            TelegramSendResult(False, error="nope"),
            TelegramSendResult(True, message_id=9),
        ]
        summary = EnterpriseTelegramService.delivery_summary(results)
        assert summary["delivered"] == 2
        assert summary["failed"] == 1
        assert summary["first_message_id"] == 5


# ── Security guards ───────────────────────────────────────────────────────────


class TestSecurityGuards:
    def test_replay_detection(self):
        service = _client()
        assert service.is_replay(111) is False
        assert service.is_replay(111) is True
        assert service.is_replay(222) is False

    def test_replay_none(self):
        service = _client()
        assert service.is_replay(None) is False

    def test_flood_disabled_by_default(self):
        assert _client().flood_guard_exceeded(1) is False

    def test_flood_guard_enabled(self):
        service = _client(messages_per_chat=2)
        assert service.flood_guard_exceeded(1) is False
        assert service.flood_guard_exceeded(1) is False
        assert service.flood_guard_exceeded(1) is True

    def test_rate_bucket(self):
        bucket = TelegramNetworkSpeed(max_per_minute=2)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False


# ── Metrics ───────────────────────────────────────────────────────────────────


class TestMetrics:
    def test_prometheus_exposition(self):
        text = append_prometheus_metrics()
        for metric in (
            "gula_telegram_sends_total",
            "gula_telegram_delivered_total",
            "gula_telegram_latency_seconds",
            "gula_telegram_webhook_received_total",
        ):
            assert metric in text
        assert "# TYPE" in text

    def test_metrics_after_send(self):
        from shared.notifications.telegram import _Metrics

        _Metrics.reset()
        service = _client()
        with patch(POST, new=lambda client, url, *, json=None, data=None, files=None: _ok_response()):
            service.send_text(123, "x")
        snap = _Metrics.snapshot()
        assert snap["delivered_total"] >= 1
        assert snap["latency_count"] >= 1


# ── Capabilities ──────────────────────────────────────────────────────────────


class TestCapabilities:
    def test_listed(self):
        caps = _client().capabilities
        for required in (
            "webhook", "groups", "topics", "channels", "inline_keyboard",
            "media_group", "rate_limit", "prometheus", "scheduled",
        ):
            assert required in caps
