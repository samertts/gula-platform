"""Unit tests for GULA-REVIEWER-001 — area review modules."""

from __future__ import annotations

import pathlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.core import Severity
from scripts.reviewer.core import ReviewFinding
from scripts.reviewer.decision import AREA_MODULES, decide


@pytest.fixture(scope="module")
def tiny_repo(tmp_path_factory) -> Path:
    """A minimal repository exercising each review area's happy and failing paths."""
    root = tmp_path_factory.mktemp("tiny-repo")
    (root / "backend" / "app" / "routes").mkdir(parents=True)
    (root / "backend" / "app" / "services").mkdir(parents=True)
    (root / "backend" / "app" / "models").mkdir(parents=True)
    (root / "backend" / "app" / "security").mkdir(parents=True)
    (root / "backend" / "app" / "audit").mkdir(parents=True)
    (root / "backend" / "tests").mkdir(parents=True)
    (root / "docs" / "adr").mkdir(parents=True)
    (root / "docs" / "brain").mkdir(parents=True)
    (root / ".ai" / "core" / "registry").mkdir(parents=True)
    (root / ".ai" / "core" / "index").mkdir(parents=True)
    (root / ".ai" / "core" / "skills").mkdir(parents=True)
    (root / ".ai" / "core" / "playbooks").mkdir(parents=True)
    (root / ".ai" / "core" / "runbooks").mkdir(parents=True)
    (root / ".ai" / "core" / "memory").mkdir(parents=True)

    (root / "backend" / "app" / "routes" / "main.py").write_text(
        "def route(): return 1\n", encoding="utf-8"
    )
    (root / "backend" / "app" / "services" / "thing.py").write_text(
        "def do():\n    return 1\n", encoding="utf-8"
    )
    (root / "backend" / "app" / "models" / "m.py").write_text(
        "id = None\n", encoding="utf-8"
    )
    (root / "backend" / "app" / "security" / "deps.py").write_text(
        "def require_permission(p):\n    return p\n", encoding="utf-8"
    )
    (root / "backend" / "app" / "audit" / "log.py").write_text(
        "def append_event():\n    return 1\n", encoding="utf-8"
    )
    (root / "backend" / "tests" / "test_thing.py").write_text(
        "def test_thing():\n    assert 1\n", encoding="utf-8"
    )
    (root / "docs" / "adr" / "ADR-0001.md").write_text(
        "# ADR-0001: Decision\nStatus: accepted\n", encoding="utf-8"
    )
    (root / "docs" / "brain" / "PROJECT_BRAIN.md").write_text(
        "# Brain\n", encoding="utf-8"
    )
    (root / "AI_OPERATING_CONSTITUTION.md").write_text(
        "# Constitution\n", encoding="utf-8"
    )
    (root / "AI_BOOTSTRAP.md").write_text("# Bootstrap\n", encoding="utf-8")
    (root / "README.md").write_text("# Readme\n", encoding="utf-8")
    (root / "ARCHITECTURE.md").write_text("# Arch\n", encoding="utf-8")
    (root / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (root / "backend" / "requirements-lock.txt").write_text("# lock\n", encoding="utf-8")
    (root / ".ai" / "core" / "registry" / "REGISTRY.md").write_text("# Registry\n", encoding="utf-8")
    (root / ".ai" / "core" / "index" / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    (root / ".ai" / "core" / "skills" / "skill.md").write_text("# Skill\n", encoding="utf-8")
    (root / ".ai" / "core" / "playbooks" / "pb.md").write_text("# PB\n", encoding="utf-8")
    (root / ".ai" / "core" / "runbooks" / "rb.md").write_text("# RB\n", encoding="utf-8")
    (root / ".ai" / "core" / "memory" / "mem.md").write_text("# Mem\n", encoding="utf-8")
    return root


class TestAreaModules:
    def test_all_modules_are_loaded(self):
        assert len(AREA_MODULES) == 8
        assert set(AREA_MODULES) == {"architecture", "code", "security", "tests",
                                     "deployment", "documentation", "performance", "knowledge"}

    def test_architecture_review_no_criticals(self, tiny_repo):
        import scripts.reviewer.architecture_review as mod
        findings = mod.review(tiny_repo)
        assert all(f.severity.value != "CRITICAL" for f in findings)
        assert any(f.title == "Module boundaries incomplete" for f in findings)

    def test_code_review_clean_small_repo(self, tiny_repo):
        import scripts.reviewer.code_review as mod
        findings = mod.review(tiny_repo)
        assert all(f.severity.value != "HIGH" for f in findings)

    def test_security_review_accepts_clean_repo(self, tiny_repo):
        import scripts.reviewer.security_review as mod
        findings = mod.review(tiny_repo)
        assert all(f.severity.value != "CRITICAL" for f in findings)

    def test_deployment_review_flags_missing_dockerfiles(self, tiny_repo):
        import scripts.reviewer.deployment_review as mod
        findings = mod.review(tiny_repo)
        assert any(f.title == "No Dockerfiles found" for f in findings)


class TestFindingsShape:
    def test_finding_has_required_fields(self):
        f = ReviewFinding("code", Severity.LOW, "title", detail="d", evidence="e", suggested_fix="fix")
        data = f.to_dict()
        assert data["area"] == "code"
        assert data["severity"] == Severity.LOW
        assert data["title"] == "title"
        assert data["detail"] == "d"
        assert data["evidence"] == "e"
        assert data["suggested_fix"] == "fix"


class TestDecideOnRepo:
    def test_decide_returns_deterministic_report(self, tiny_repo):
        r1 = decide(tiny_repo, target="tiny")
        r2 = decide(tiny_repo, target="tiny")
        assert r1.decision == r2.decision
        assert r1.overall_score == r2.overall_score
        assert r1.target == "tiny"
        assert len(r1.area_reviews) == 8

    def test_report_all_findings_flat(self, tiny_repo):
        r = decide(tiny_repo)
        flat = r.all_findings()
        assert len(flat) == sum(len(a.findings) for a in r.area_reviews)
