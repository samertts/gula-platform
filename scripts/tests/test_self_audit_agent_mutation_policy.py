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


def test_impact_selector_finds_import_matched_test_without_exact_name(tmp_path, monkeypatch):
    """No tests/test_widget2.py exists, but some other test file imports
    app.widget2 directly -- the reverse-dependency tier must find it and
    report a weaker-but-still-deterministic confidence, not fall straight
    to UNKNOWN/full-suite."""
    backend = _make_fake_repo(tmp_path, monkeypatch)
    (backend / "app" / "widget2.py").write_text("VALUE = 1\n")
    other_test = backend / "tests" / "test_something_else.py"
    other_test.write_text("from app.widget2 import VALUE\n\ndef test_x():\n    assert VALUE == 1\n")

    args, confidence = saa._select_impact_aware_tests([backend / "app" / "widget2.py"])

    assert confidence == "IMPORT_MATCHED"
    assert args == ["tests/test_something_else.py"]


# ─── Syntax verification targets the ACTUAL changed file ───────────────────


def test_verify_catches_syntax_error_in_the_actual_changed_file(tmp_path, monkeypatch):
    """A file broken by _apply_auto_fixes must be caught by its OWN syntax
    check. There is deliberately no app/main.py anywhere in this fake
    repo -- if the old hardcoded-app/main.py check were still in place,
    this would either miss the real defect or fail for the wrong reason
    (a missing file), not because THIS file is broken."""
    backend = _make_fake_repo(tmp_path, monkeypatch)
    target = backend / "app" / "widget.py"
    target.write_text("import os\n")

    result = saa._apply_auto_fixes([
        {"file": "app/widget.py", "search": "import os", "replace": "import os (((broken", "reason": "demo"},
    ])
    assert result.applied

    ok, confidence = saa._verify_after_fix(list(result.snapshots.keys()))

    assert ok is False
    assert confidence == "syntax_check_failed"


def test_verify_checks_the_changed_file_directly_not_a_fixed_stand_in(tmp_path, monkeypatch):
    """A valid change to a file, with no app/main.py present at all in
    this fake repo, must NOT fail on a syntax check -- proving the
    verification target is the changed file itself, not a fixed path
    that happens not to exist here."""
    backend = _make_fake_repo(tmp_path, monkeypatch)
    target = backend / "app" / "widget.py"
    target.write_text("VALUE = 1\n")
    (backend / "tests" / "test_widget.py").write_text("def test_x(): pass\n")
    assert not (backend / "app" / "main.py").exists()

    result = saa._apply_auto_fixes([
        {"file": "app/widget.py", "search": "VALUE = 1", "replace": "VALUE = 2", "reason": "demo"},
    ])
    assert result.applied

    ok, confidence = saa._verify_after_fix(list(result.snapshots.keys()))

    assert confidence != "syntax_check_failed"
    assert ok is True
    assert confidence == "TARGETED"


# ─── Verification failure prevents commit ──────────────────────────────────


def test_verification_failure_rolls_back_and_never_commits(tmp_path, monkeypatch):
    """Mirrors run_audit()'s real control flow: apply -> verify -> commit
    only on success, else rollback. A broken change must never reach
    _commit_fixes."""
    backend = _make_fake_repo(tmp_path, monkeypatch)
    target = backend / "app" / "widget.py"
    original = "import os\n"
    target.write_text(original)

    commit_calls: list[object] = []
    monkeypatch.setattr(
        saa, "_commit_fixes",
        lambda *a, **k: commit_calls.append((a, k)) or True,
    )

    result = saa._apply_auto_fixes([
        {"file": "app/widget.py", "search": "import os", "replace": "import os (((broken", "reason": "demo"},
    ])
    ok, _confidence = saa._verify_after_fix(list(result.snapshots.keys()))

    if ok:
        saa._commit_fixes(result.applied, list(result.snapshots.keys()))
    else:
        saa._rollback_exact(result.snapshots)

    assert ok is False
    assert commit_calls == []  # _commit_fixes was never invoked
    assert target.read_text() == original  # exact rollback, not a partial/committed state
