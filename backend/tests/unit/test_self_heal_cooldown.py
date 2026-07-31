from __future__ import annotations

import json
import os
import pathlib
import sys
import types

os.environ.setdefault("ENV", "test")

# scripts/self_heal.py imports `requests`/`urllib3`. When they are not
# installed (lean CI environments), fall back to stub modules so the
# import chain still resolves. When they ARE installed (opentelemetry
# dependency), leave them alone — stubbing would shadow the real packages
# and poison later tests (e.g. OTel exporter imports requests.exceptions).
for _dep in ("requests", "urllib3"):
    if _dep not in sys.modules:
        try:
            __import__(_dep)
        except ImportError:
            sys.modules[_dep] = types.ModuleType(_dep)

if "urllib3" in sys.modules:
    _u3 = sys.modules["urllib3"]
    if not hasattr(_u3, "exceptions"):
        _exc = types.ModuleType("urllib3.exceptions")
        _exc.InsecureRequestWarning = type("InsecureRequestWarning", (Warning,), {})
        _u3.exceptions = _exc
    if not hasattr(_u3, "disable_warnings"):
        _u3.disable_warnings = lambda *_a, **_k: None

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts import self_heal  # noqa: E402


def test_action_due_first_call(tmp_path: pathlib.Path) -> None:
    self_heal.COOLDOWN_FILE = tmp_path / "cooldown.json"
    self_heal.ACTION_COOLDOWN_S = 600
    assert self_heal._action_due("api_unreachable", "restart_backend") is True


def test_action_due_cooldown_blocks_second_call(tmp_path: pathlib.Path) -> None:
    self_heal.COOLDOWN_FILE = tmp_path / "cooldown.json"
    self_heal.ACTION_COOLDOWN_S = 600
    self_heal._action_due("api_unreachable", "restart_backend")
    assert self_heal._action_due("api_unreachable", "restart_backend") is False


def test_action_due_after_cooldown_expiry(tmp_path: pathlib.Path) -> None:
    self_heal.COOLDOWN_FILE = tmp_path / "cooldown.json"
    self_heal.ACTION_COOLDOWN_S = 0.1
    self_heal._action_due("api_unreachable", "restart_backend")
    import time

    time.sleep(0.15)
    assert self_heal._action_due("api_unreachable", "restart_backend") is True


def test_action_due_different_signals_independent(tmp_path: pathlib.Path) -> None:
    self_heal.COOLDOWN_FILE = tmp_path / "cooldown.json"
    self_heal.ACTION_COOLDOWN_S = 600
    self_heal._action_due("api_unreachable", "restart_backend")
    assert self_heal._action_due("db_very_slow", "restart_backend") is True


def test_cooldown_persists_across_processes(tmp_path: pathlib.Path) -> None:
    cooldown_file = tmp_path / "cooldown.json"
    self_heal.COOLDOWN_FILE = cooldown_file
    self_heal.ACTION_COOLDOWN_S = 600
    self_heal._action_due("queue_exploded", "restart_worker")
    data = json.loads(cooldown_file.read_text())
    assert "queue_exploded:restart_worker" in data


def test_corrupted_cooldown_file_recovers(tmp_path: pathlib.Path) -> None:
    cooldown_file = tmp_path / "cooldown.json"
    cooldown_file.write_text("{not json")
    self_heal.COOLDOWN_FILE = cooldown_file
    self_heal.ACTION_COOLDOWN_S = 600
    assert self_heal._action_due("api_unreachable", "restart_backend") is True
    assert self_heal._action_due("api_unreachable", "restart_backend") is False


def test_missing_cooldown_file_recovers(tmp_path: pathlib.Path) -> None:
    self_heal.COOLDOWN_FILE = tmp_path / "does-not-exist.json"
    self_heal.ACTION_COOLDOWN_S = 600
    assert self_heal._action_due("api_unreachable", "restart_backend") is True


def test_execute_respects_cooldown(tmp_path: pathlib.Path, monkeypatch) -> None:
    self_heal.COOLDOWN_FILE = tmp_path / "cooldown.json"
    self_heal.ACTION_COOLDOWN_S = 600
    taken_actions: list[str] = []
    monkeypatch.setattr(self_heal, "restart_service", lambda name: taken_actions.append(name) or True)
    monkeypatch.setattr(self_heal.time, "sleep", lambda _s: None)

    signal = self_heal.Signal("api_unreachable", False, risk=self_heal.Risk.HIGH)
    decision = self_heal.Decision(
        signal=signal, actions=["restart_backend"], risk=self_heal.Risk.HIGH, rationale="test"
    )
    self_heal.execute(decision)
    assert taken_actions == ["gula-backend"]
    self_heal.execute(decision)
    assert taken_actions == ["gula-backend"], "second execution must be suppressed by cooldown"
