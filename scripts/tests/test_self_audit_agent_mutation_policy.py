"""Behavioral proof for self_audit_agent.py's autonomous-mutation safety
policy: path allow-list, change budget, exact-scope rollback, and
impact-aware verification falling back safely on unknown evidence.

Each test builds a throwaway fake repo under tmp_path and monkeypatches
the module's REPO_ROOT/BACKEND_DIR so the real functions run against it
unmodified -- these are the actual functions self_audit_agent.py's
--fix path calls, not a reimplementation.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from scripts import self_audit_agent as saa


def _make_fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    backend = tmp_path / "backend"
    (backend / "app").mkdir(parents=True)
    (backend / "app" / "security").mkdir()
    (backend / "tests").mkdir()
    (tmp_path / "backend" / "migrations").mkdir()
    monkeypatch.setattr(saa, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(saa, "BACKEND_DIR", backend)
    return backend


# ─── Path allow-list ────────────────────────────────────────────────────────


def test_protected_path_is_rejected_without_writing_anything(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    target = backend / "app" / "security" / "auth.py"
    target.write_text("SECRET = 'do-not-touch'\n")

    result = saa._apply_auto_fixes([
        {"file": "app/security/auth.py", "search": "SECRET", "replace": "PUBLIC", "reason": "demo"},
    ])

    assert result.applied == []
    assert any("protected path" in r for r in result.rejected)
    assert target.read_text() == "SECRET = 'do-not-touch'\n"  # untouched


def test_path_traversal_outside_repo_is_rejected(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    outside = tmp_path.parent / "outside_the_repo.py"
    outside.write_text("x = 1\n")
    try:
        result = saa._apply_auto_fixes([
            {"file": "../outside_the_repo.py", "search": "x = 1", "replace": "x = 2", "reason": "demo"},
        ])
        assert result.applied == []
        assert outside.read_text() == "x = 1\n"  # untouched
    finally:
        outside.unlink(missing_ok=True)


def test_stale_search_text_is_rejected_not_silently_skipped(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    target = backend / "app" / "widget.py"
    target.write_text("def f():\n    return 1\n")

    result = saa._apply_auto_fixes([
        {"file": "app/widget.py", "search": "return 2", "replace": "return 3", "reason": "demo"},
    ])
    assert result.applied == []
    assert any("stale" in r for r in result.rejected)


# ─── Change budget ──────────────────────────────────────────────────────────


def test_budget_stops_execution_after_max_files_per_run(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(saa, "MAX_FILES_PER_RUN", 2)
    fixes = []
    for i in range(5):
        p = backend / "app" / f"m{i}.py"
        p.write_text(f"VALUE = {i}\n")
        fixes.append({"file": f"app/m{i}.py", "search": f"VALUE = {i}", "replace": f"VALUE = {i + 100}", "reason": "demo"})

    result = saa._apply_auto_fixes(fixes)

    assert len(result.applied) == 2
    assert any("budget exceeded" in r for r in result.rejected)
    # the 3 over-budget files must be byte-identical to their original content
    for i in range(2, 5):
        assert (backend / "app" / f"m{i}.py").read_text() == f"VALUE = {i}\n"


def test_oversized_single_change_is_rejected(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(saa, "MAX_CHARS_CHANGED_PER_FILE", 10)
    target = backend / "app" / "widget.py"
    target.write_text("SMALL = 1\n")

    result = saa._apply_auto_fixes([
        {"file": "app/widget.py", "search": "SMALL = 1", "replace": "SMALL = 1  # " + ("x" * 200), "reason": "demo"},
    ])
    assert result.applied == []
    assert any("exceeds MAX_CHARS_CHANGED_PER_FILE" in r for r in result.rejected)


# ─── Exact-scope rollback: the core negative proof ─────────────────────────


def test_rollback_restores_exact_file_and_preserves_unrelated_changes(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    target = backend / "app" / "widget.py"
    target.write_text("VALUE = 1\n")
    unrelated = backend / "app" / "unrelated.py"
    unrelated.write_text("UNTOUCHED = True\n")

    result = saa._apply_auto_fixes([
        {"file": "app/widget.py", "search": "VALUE = 1", "replace": "VALUE = 2", "reason": "demo"},
    ])
    assert result.applied  # the fix WAS applied
    assert target.read_text() == "VALUE = 2\n"

    # simulate an unrelated, concurrent edit landing in the tree between
    # apply and verify -- exactly the scenario a broad `git checkout -- .`
    # would destroy.
    unrelated.write_text("UNTOUCHED = True  # edited concurrently\n")

    saa._rollback_exact(result.snapshots)

    assert target.read_text() == "VALUE = 1\n"  # exact rollback
    assert unrelated.read_text() == "UNTOUCHED = True  # edited concurrently\n"  # preserved


def test_rollback_is_idempotent(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    target = backend / "app" / "widget.py"
    target.write_text("VALUE = 1\n")
    result = saa._apply_auto_fixes([
        {"file": "app/widget.py", "search": "VALUE = 1", "replace": "VALUE = 2", "reason": "demo"},
    ])

    saa._rollback_exact(result.snapshots)
    saa._rollback_exact(result.snapshots)  # calling it twice must not error or change the outcome

    assert target.read_text() == "VALUE = 1\n"


# ─── Impact-aware verification: unknown must broaden, never skip ──────────


def test_impact_selector_finds_targeted_test_when_it_exists(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    (backend / "app" / "widget.py").write_text("VALUE = 1\n")
    (backend / "tests" / "test_widget.py").write_text("def test_x(): pass\n")

    args, confidence = saa._select_impact_aware_tests([backend / "app" / "widget.py"])

    assert confidence == "TARGETED"
    assert args == ["tests/test_widget.py"]


def test_impact_selector_reports_unknown_when_no_test_maps(tmp_path, monkeypatch):
    backend = _make_fake_repo(tmp_path, monkeypatch)
    (backend / "app" / "orphan.py").write_text("VALUE = 1\n")
    # deliberately no tests/test_orphan.py

    args, confidence = saa._select_impact_aware_tests([backend / "app" / "orphan.py"])

    assert confidence == "UNKNOWN"
    assert args == []
