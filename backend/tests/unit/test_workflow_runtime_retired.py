"""Regression tests — PROGRAM-01 Wave 4 Commit 3.6 (order 19, ADR-036).

Asserts the broken `national/workflow_runtime` package is fully retired while
the canonical `WorkflowEngine` surface stays intact and wired.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestNamespaceVacated:
    def test_workflow_runtime_namespace_gone(self):
        assert importlib.util.find_spec("app.national.workflow_runtime") is None

    def test_platform_workflow_gone(self):
        assert importlib.util.find_spec("app.platform.workflow") is None

    def test_factory_no_longer_imports_workflow_runtime(self):
        src = (REPO_ROOT / "backend/app/factory.py").read_text(encoding="utf-8")
        assert "workflow_runtime" not in src

    def test_archived_files_present_with_headers(self):
        for name in (
            "national_workflow_runtime_init.py",
            "national_workflow_runtime_api_routes.py",
            "national_workflow_runtime_application_service.py",
            "national_workflow_runtime_domain_saga_engine.py",
            "national_workflow_runtime_infrastructure_repository.py",
            "platform_workflow.py",
        ):
            p = REPO_ROOT / "archive/platform-shared-core" / name
            assert p.exists(), name
            assert p.read_text(encoding="utf-8").startswith('"""Archived Shared Core')

    def test_zero_byte_service_evidence_documented(self):
        p = REPO_ROOT / "archive/platform-shared-core/national_workflow_runtime_application_service.py"
        text = p.read_text(encoding="utf-8")
        assert "0 bytes" in text
        assert "WorkflowRuntimeService" in text

    def test_frontend_client_no_workflow_runtime(self):
        client = (REPO_ROOT / "frontend-v3/src/api/generated/client.ts").read_text(encoding="utf-8")
        assert "workflow_runtime" not in client
        assert "workflow-runtime" not in client

    def test_frontend_routes_and_nav_no_workflow_runtime(self):
        routes = (REPO_ROOT / "frontend-v3/src/routes/index.tsx").read_text(encoding="utf-8")
        nav = (REPO_ROOT / "frontend-v3/src/permissions/index.ts").read_text(encoding="utf-8")
        assert "workflow-runtime" not in routes
        assert "workflow-runtime" not in nav

    def test_scripts_registries_no_workflow_runtime(self):
        gen = (REPO_ROOT / "scripts/generate_frontend_client.py").read_text(encoding="utf-8")
        drift = (REPO_ROOT / "scripts/zero_drift_engine.py").read_text(encoding="utf-8")
        assert "workflow_runtime" not in gen
        assert "workflow_runtime" not in drift


class TestCanonicalProviderIntact:
    def test_canonical_engine_importable(self):
        from app.workflows.engine import WorkflowEngine

        assert WorkflowEngine.__name__ == "WorkflowEngine"

    def test_niam_workflows_router_wired(self):
        from app.identity.workflows.routes import router as workflows_router

        assert workflows_router.prefix == "/workflows"
        assert len(workflows_router.routes) > 0


class TestBrokenSurfaceRetired:
    def test_archived_routes_declare_the_broken_surface(self):
        text = (REPO_ROOT / "archive/platform-shared-core/national_workflow_runtime_api_routes.py").read_text(
            encoding="utf-8"
        )
        assert "definitions" in text
        assert "executions" in text
        assert "templates" in text

    def test_no_execute_workflow_signal_remains_in_backend_app(self):
        pattern = re.compile(r"def\s+execute_workflow\s*\(")
        hits = []
        for path in (REPO_ROOT / "backend/app").rglob("*.py"):
            if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
                hits.append(str(path.relative_to(REPO_ROOT)))
        assert hits == []

    def test_no_workflow_runtime_reference_in_backend_app(self):
        hits = []
        for path in (REPO_ROOT / "backend/app").rglob("*.py"):
            if "workflow_runtime" in path.read_text(encoding="utf-8", errors="replace"):
                hits.append(str(path.relative_to(REPO_ROOT)))
        assert hits == []


class TestArchiveHeaderReferences:
    def test_archive_headers_document_source_and_reversibility(self):
        p = REPO_ROOT / "archive/platform-shared-core/national_workflow_runtime_api_routes.py"
        text = p.read_text(encoding="utf-8")
        assert "backend/app/national/workflow_runtime/api/routes.py" in text
        assert "ADR-036" in text
        assert "revert" in text
