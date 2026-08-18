"""Duty lifecycle cache and clinical channel revocation tests."""
from app.services.doctor_duty_lifecycle import DutyLifecycleRegistry


def test_revoke_clears_registered_keys_and_calls_stop_callbacks(monkeypatch):
    registry = DutyLifecycleRegistry()
    deleted = []
    stopped = []
    monkeypatch.setattr("app.services.doctor_duty_lifecycle.delete_cache", lambda key: deleted.append(key) or True)
    registry.register_cache_key("dctx-1", "opaque-cache-key")
    registry.register_stop_callback("dctx-1", lambda: stopped.append("speech"))
    registry.register_stop_callback("dctx-1", lambda: stopped.append("notifications"))

    result = registry.revoke("dctx-1")

    assert deleted == ["opaque-cache-key"]
    assert stopped == ["speech", "notifications"]
    assert result == {"cache_keys_invalidated": 1, "stop_callbacks_called": 2}
    assert registry.revoke("dctx-1") == {"cache_keys_invalidated": 0, "stop_callbacks_called": 0}


def test_failed_stop_callback_does_not_keep_access(monkeypatch):
    registry = DutyLifecycleRegistry()
    monkeypatch.setattr("app.services.doctor_duty_lifecycle.delete_cache", lambda key: True)
    registry.register_cache_key("dctx-2", "opaque-cache-key")
    registry.register_stop_callback("dctx-2", lambda: (_ for _ in ()).throw(RuntimeError("channel unavailable")))

    result = registry.revoke("dctx-2")

    assert result == {"cache_keys_invalidated": 1, "stop_callbacks_called": 0}
    assert registry.revoke("dctx-2") == {"cache_keys_invalidated": 0, "stop_callbacks_called": 0}
