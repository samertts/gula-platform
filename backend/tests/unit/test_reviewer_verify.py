"""Unit tests for GULA-REVIEWER-001 — change-set verification (reviewer-verify)."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.reviewer import verify
from scripts.reviewer.verify import (
    MissionInfo,
    changeset_files,
    check_architecture,
    check_code,
    check_deployment,
    check_documentation,
    check_knowledge,
    check_performance,
    check_security,
    check_tests,
    gate,
    resolve_mission,
    review_changeset,
    write_report,
)


def _p(tmp_path, rel: str, content: str = "") -> pathlib.Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _rel(rel: str) -> pathlib.Path:
    """Repo-relative path for the scoped checks (checks resolve via REPO_ROOT)."""
    return pathlib.Path(rel)


class TestResolveMission:
    def test_unknown_mission_not_found(self):
        info = resolve_mission("__UNKNOWN__")
        assert info.found is False
        assert info.mission_id == "__UNKNOWN__"

    def test_empty_mission_id_not_found(self):
        assert resolve_mission("").found is False

    def test_known_mission_from_registry(self, tmp_path, monkeypatch):
        import json

        registry = tmp_path / "registry.json"
        registry.write_text(json.dumps({"missions": {
            "MSN-ABC": {
                "objective": "Fix login crash",
                "mission_type": "bug",
                "status": "routed",
                "files": ["backend/app/routes/admin.py"],
            }
        }}), encoding="utf-8")
        monkeypatch.setattr(verify, "ORCHESTRATOR_REGISTRY", registry)
        info = resolve_mission("msn-abc")
        assert info.found is True
        assert info.mission_type == "bug"
        assert info.objective == "Fix login crash"
        assert info.recorded_files == ["backend/app/routes/admin.py"]

    def test_case_insensitive_match(self, tmp_path, monkeypatch):
        import json

        registry = tmp_path / "registry.json"
        registry.write_text(json.dumps({"missions": {
            "ORN-1E9C0FE9": {"objective": "x", "mission_type": "feature",
                             "status": "routed", "files": []}
        }}), encoding="utf-8")
        monkeypatch.setattr(verify, "ORCHESTRATOR_REGISTRY", registry)
        assert resolve_mission("orn-1e9c0fe9").found is True

    def test_recorded_files_optional(self, tmp_path, monkeypatch):
        import json

        registry = tmp_path / "registry.json"
        registry.write_text(json.dumps({"missions": {
            "MSN-NO-FILES": {"objective": "x", "mission_type": "feature"}
        }}), encoding="utf-8")
        monkeypatch.setattr(verify, "ORCHESTRATOR_REGISTRY", registry)
        assert resolve_mission("MSN-NO-FILES").recorded_files == []

    def test_missing_registry_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "ORCHESTRATOR_REGISTRY", tmp_path / "nope.json")
        assert resolve_mission("MSN-ABC").found is False


class TestChangesetFiles:
    def test_explicit_files_are_resolved(self, tmp_path, monkeypatch):
        _p(tmp_path, "backend/app/routes/x.py")
        _p(tmp_path, "backend/app/services/x_service.py")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        mission = MissionInfo(mission_id="MSN-X")
        paths = changeset_files(mission, explicit=(
            "backend/app/routes/x.py", "backend/app/routes/missing.py",
        ))
        assert [p.as_posix() for p in paths] == ["backend/app/routes/x.py"]

    def test_missing_files_filtered(self, tmp_path, monkeypatch):
        _p(tmp_path, "a.py")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        mission = MissionInfo(mission_id="MSN-X")
        paths = changeset_files(mission, explicit=("a.py", "b.py"))
        assert [p.as_posix() for p in paths] == ["a.py"]

    def test_deduplicates_and_sorts(self, tmp_path, monkeypatch):
        _p(tmp_path, "b.py")
        _p(tmp_path, "a.py")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        mission = MissionInfo(mission_id="MSN-X")
        paths = changeset_files(mission, explicit=("b.py", "a.py", "a.py"))
        assert [p.as_posix() for p in paths] == ["a.py", "b.py"]

    def test_uses_git_fallback(self, tmp_path, monkeypatch):
        _p(tmp_path, "backend/app/x.py")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(verify, "_git",
                            lambda args: ["backend/app/x.py"])
        mission = MissionInfo(mission_id="MSN-X")
        paths = changeset_files(mission, use_git=True)
        assert [p.as_posix() for p in paths] == ["backend/app/x.py"]

    def test_recorded_files_used(self, tmp_path, monkeypatch):
        _p(tmp_path, "backend/app/recorded.py")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        mission = MissionInfo(mission_id="MSN-X",
                              recorded_files=["backend/app/recorded.py"])
        paths = changeset_files(mission)
        assert [p.as_posix() for p in paths] == ["backend/app/recorded.py"]

    def test_empty_without_sources(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(verify, "_git", lambda args: [])
        mission = MissionInfo(mission_id="MSN-X")
        assert changeset_files(mission) == []


class TestScopedChecks:
    def test_architecture_route_without_service(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/routes/new.py", "def r():\n    pass\n")
        path = _rel("backend/app/routes/new.py")
        findings = check_architecture([path])
        assert any(f.area == "architecture" and f.severity.value == "medium"
                   and "new_service.py" in f.detail for f in findings)

    def test_architecture_route_with_service_ok(self, tmp_path, monkeypatch):
        _p(tmp_path, "backend/app/services/new_service.py", "def s():\n    pass\n")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/routes/new.py", "def r():\n    pass\n")
        path = _rel("backend/app/routes/new.py")
        assert check_architecture([path]) == []

    def test_architecture_layer_inversion_high(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/services/evil.py", "from ..routes import x\n")
        path = _rel("backend/app/services/evil.py")
        findings = check_architecture([path])
        assert any(f.severity.value == "high" and "Layer inversion" in f.title
                   for f in findings)

    def test_code_unsafe_pattern_high(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/unsafe.py", "eval(x)\n")
        path = _rel("backend/app/unsafe.py")
        findings = check_code([path])
        assert any(f.severity.value == "high" and "eval" in f.title
                   for f in findings)

    def test_code_dead_markers_low(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/marked.py", "# TODO fix\n")
        path = _rel("backend/app/marked.py")
        findings = check_code([path])
        assert any(f.severity.value == "low" and "Dead-code" in f.title
                   for f in findings)

    def test_code_clean_file_no_findings(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/clean.py", "def clean():\n    return 1\n")
        path = _rel("backend/app/clean.py")
        assert check_code([path]) == []

    def test_security_hardcoded_secret_high(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/secrets.py", "PASSWORD = 'super-secret-value'\n")
        path = _rel("backend/app/secrets.py")
        findings = check_security([path])
        assert any(f.severity.value == "high"
                   and "hardcoded credential" in f.title for f in findings)

    def test_security_skips_tests(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/tests/test_secrets.py", "PASSWORD = 'fixture-value'\n")
        path = _rel("backend/tests/test_secrets.py")
        assert check_security([path]) == []

    def test_security_clean(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/ok.py", "x = 1\n")
        path = _rel("backend/app/ok.py")
        assert check_security([path]) == []

    def test_tests_missing_for_module(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/services/foo_service.py", "def f():\n    pass\n")
        path = _rel("backend/app/services/foo_service.py")
        findings = check_tests([path])
        assert any(f.area == "tests" and f.severity.value == "medium"
                   for f in findings)

    def test_tests_present_ok(self, tmp_path, monkeypatch):
        _p(tmp_path, "backend/tests/unit/test_foo_service.py", "def test_f():\n    pass\n")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/services/foo_service.py", "def f():\n    pass\n")
        path = _rel("backend/app/services/foo_service.py")
        assert check_tests([path]) == []

    def test_tests_engine_mapping(self, tmp_path, monkeypatch):
        _p(tmp_path, "backend/tests/unit/test_optimizer_core.py", "def test_x():\n    pass\n")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        path = _rel("scripts/optimizer/core.py")
        assert check_tests([path]) == []

    def test_documentation_public_change_without_docs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/routes/x.py", "def r():\n    pass\n")
        path = _rel("backend/app/routes/x.py")
        findings = check_documentation([path])
        assert any(f.area == "documentation" and "lacks documentation" in f.title
                   for f in findings)

    def test_documentation_ok_with_docs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        doc = _p(tmp_path, "docs/feature.md", "# feature\n")
        code = _rel("backend/app/routes/x.py")
        assert check_documentation([doc, code]) == []

    def test_deployment_infra_without_docs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/Dockerfile", "FROM python:3.12\n")
        path = _rel("backend/Dockerfile")
        findings = check_deployment([path])
        assert any(f.area == "deployment" and "lacks documentation" in f.title
                   for f in findings)

    def test_deployment_ok_with_docs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        docker = _rel("backend/Dockerfile")
        doc = _rel("docs/deploy.md")
        assert check_deployment([docker, doc]) == []

    def test_performance_large_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        content = "\n".join(f"# line {i}" for i in range(900))
        _p(tmp_path, "backend/app/big.py", content)
        path = _rel("backend/app/big.py")
        findings = check_performance([path])
        assert any(f.area == "performance" and "Oversized" in f.title
                   for f in findings)

    def test_performance_small_file_ok(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "backend/app/small.py", "def f():\n    pass\n")
        path = _rel("backend/app/small.py")
        assert check_performance([path]) == []

    def test_knowledge_registry_not_updated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        _p(tmp_path, "scripts/optimizer/core.py", "CONST = 1\n")
        path = _rel("scripts/optimizer/core.py")
        findings = check_knowledge([path])
        assert any(f.area == "knowledge" and "Registry/index" in f.title
                   for f in findings)

    def test_knowledge_ok_with_registry(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        script = _rel("scripts/optimizer/core.py")
        registry = _rel(".ai/core/registry/REGISTRY.md")
        assert check_knowledge([script, registry]) == []


class TestReviewChangeset:
    def test_empty_change_set_rejects(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(verify, "_git", lambda args: [])
        report, _mission, paths = review_changeset("MSN-NOTHING")
        assert report.decision == "REJECT"
        assert report.target == "changeset:MSN-NOTHING"
        assert report.mission_id == "MSN-NOTHING"
        assert paths == []

    def test_clean_changeset_passes(self, tmp_path, monkeypatch):
        _p(tmp_path, "backend/tests/unit/test_foo_service.py", "def test_f():\n    pass\n")
        _p(tmp_path, "backend/app/services/foo_service.py", "def f():\n    pass\n")
        _p(tmp_path, "docs/feature.md", "# feature\n")
        _p(tmp_path, ".ai/core/registry/REGISTRY.md", "# Registry\n")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        report, _mission, paths = review_changeset(
            "MSN-OK",
            explicit_files=(
                "backend/app/services/foo_service.py",
                "backend/tests/unit/test_foo_service.py",
                "docs/feature.md",
                ".ai/core/registry/REGISTRY.md",
            ),
        )
        assert report.decision == "PASS"
        assert report.overall_score == 100.0
        assert len(paths) == 4

    def test_gate_semantics(self):
        from scripts.reviewer.core import AreaReview, Decision, ReviewFinding, Severity

        clean = [AreaReview("architecture", [], 100.0, Decision.PASS.value)
                 for _ in range(8)]
        rejecting = list(clean)
        rejecting[0] = AreaReview(
            "architecture",
            [ReviewFinding("architecture", Severity.HIGH, "x", detail="y")],
            85.0, Decision.REJECT.value,
        )

        class _Report:
            decision = Decision.PASS.value

        assert gate(_Report()) == 0

        import types

        reject_report = types.SimpleNamespace(decision=Decision.REJECT.value)
        assert gate(reject_report) == 1

    def test_reviewed_at_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(verify, "_git", lambda args: [])
        report, _, _ = review_changeset("MSN-NOTHING")
        assert report.reviewed_at

    def test_write_report_renders_files(self, tmp_path, monkeypatch):
        _p(tmp_path, "backend/app/services/foo_service.py", "def f():\n    pass\n")
        _p(tmp_path, "backend/tests/unit/test_foo_service.py", "def test_f():\n    pass\n")
        _p(tmp_path, "docs/feature.md", "# feature\n")
        _p(tmp_path, ".ai/core/registry/REGISTRY.md", "# Registry\n")
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(verify, "REVIEWER_VERIFY_PATH", tmp_path / "verify.md")
        monkeypatch.setattr(verify, "STATE_DIR", tmp_path / "state")
        report, _, paths = review_changeset(
            "MSN-WRITE",
            explicit_files=(
                "backend/app/services/foo_service.py",
                "backend/tests/unit/test_foo_service.py",
                "docs/feature.md",
                ".ai/core/registry/REGISTRY.md",
            ),
        )
        written = write_report(report, paths)
        text = written.read_text(encoding="utf-8")
        assert "REVIEWER_VERIFY_REPORT.md" in text
        assert "MSN-WRITE" in text
        assert "backend/app/services/foo_service.py" in text
        assert (tmp_path / "state" / "latest_verify.json").exists()


class TestCli:
    def test_verify_command_registered(self):
        from scripts.reviewer import cli

        assert "reviewer-verify" in cli.REVIEWER_COMMANDS

    def test_verify_missing_mission_returns_usage(self, capsys, monkeypatch):
        import sys

        monkeypatch.setattr(sys, "argv", ["reviewer.py", "verify"])
        from scripts.reviewer import cli

        assert cli.run_verify() == 2
        captured = capsys.readouterr()
        assert "Usage: reviewer-verify" in captured.out

    def test_verify_unknown_mission_rejects(self, capsys, tmp_path, monkeypatch):
        import sys

        _p(tmp_path, "backend/app/services/foo_service.py", "def f():\n    pass\n")
        monkeypatch.setattr(sys, "argv", [
            "reviewer.py", "verify", "MSN-UNKNOWN",
            "backend/app/services/foo_service.py",
        ])
        monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(verify, "REVIEWER_VERIFY_PATH", tmp_path / "verify.md")
        monkeypatch.setattr(verify, "STATE_DIR", tmp_path / "state")
        from scripts.reviewer import cli

        assert cli.run_verify() == 0
        captured = capsys.readouterr()
        assert "[warn] mission MSN-UNKNOWN not found" in captured.out
        assert "[OK] verify.md written" in captured.out

    def test_kernel_exposes_verify(self):
        from scripts.kernel import cli as kernel_cli

        assert "reviewer-verify" in kernel_cli.COMMANDS
