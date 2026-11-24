"""Regression tests for the canonical NIAM workflow integration (CR-1).

Verifies the local ``app.workflows`` runtime is the single active workflow
implementation: the remote ``national/workflow_runtime`` namespace and the
duplicate ``identity/workflows/{engine,models}`` copies are retired, the
canonical router is mounted exactly once, authorization is enforced, and the
``get_niam_db`` async-compatibility bridge works with the workflow engine.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from app.database import AsyncCompatSession
from app.identity.base import IdentityBase
from app.identity.security import get_current_identity
from app.identity.workflows import routes as workflows_routes
from app.workflows import models as workflow_models
from app.workflows.engine import WorkflowEngine
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestNamespaceRetired:
    def test_national_workflow_runtime_removed(self):
        assert importlib.util.find_spec("app.national.workflow_runtime") is None

    def test_duplicate_identity_engine_removed(self):
        assert importlib.util.find_spec("app.identity.workflows.engine") is None
        assert importlib.util.find_spec("app.identity.workflows.models") is None

    def test_platform_workflow_removed(self):
        assert importlib.util.find_spec("app.platform.workflow") is None

    def test_factory_has_no_workflow_runtime_import(self):
        source = (REPO_ROOT / "backend/app/factory.py").read_text(encoding="utf-8")
        assert "workflow_runtime" not in source

    def test_active_app_has_no_stale_workflow_refs(self):
        active = REPO_ROOT / "backend/app"
        offenders = []
        for path in active.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if (
                "national.workflow_runtime" in text
                or "identity.workflows.engine" in text
                or "identity.workflows.models" in text
            ):
                offenders.append(str(path.relative_to(REPO_ROOT)))
        assert offenders == []


class TestRouterRegisteredOnce:
    def test_router_prefix_and_endpoints(self):
        assert workflows_routes.router.prefix == "/workflows"
        paths = {route.path for route in workflows_routes.router.routes}
        assert paths == {
            "/workflows/definitions",
            "/workflows/definitions/{def_id}",
            "/workflows/instances",
            "/workflows/instances/{instance_id}",
            "/workflows/instances/{instance_id}/approve",
            "/workflows/instances/{instance_id}/cancel",
            "/workflows/approvals/pending/{approver_id}",
        }

    def test_identity_router_includes_workflows_exactly_once(self):
        from app.identity.api.router import router as identity_router

        included = [
            route
            for route in identity_router.routes
            if getattr(route, "original_router", None) is workflows_routes.router
        ]
        assert len(included) == 1

    def test_router_requires_authentication(self):
        app = FastAPI()
        app.include_router(workflows_routes.router)
        client = TestClient(app)
        response = client.get("/workflows/definitions")
        assert response.status_code == 401


class TestWorkflowDatabaseIntegration:
    @pytest.fixture
    def session(self, tmp_path):
        engine = create_engine(f"sqlite:///{tmp_path / 'workflows.db'}")
        workflow_tables = [
            workflow_models.WorkflowDefinition.__table__,
            workflow_models.WorkflowInstance.__table__,
            workflow_models.WorkflowApproval.__table__,
            workflow_models.WorkflowNotification.__table__,
        ]
        IdentityBase.metadata.create_all(engine, tables=workflow_tables)
        sync_session = Session(engine)
        yield AsyncCompatSession(sync_session)
        sync_session.close()
        engine.dispose()

    def test_create_and_list_definition(self, session):
        import asyncio

        async def scenario():
            engine = WorkflowEngine(session)
            definition = await engine.create_definition(
                def_id="def-1",
                name="Lab approval",
                workflow_type="approval",
                steps=[{"name": "review", "approver_role": "admin"}],
            )
            assert definition.def_id == "def-1"
            await session.commit()

            fetched = await engine.get_definition("def-1")
            assert fetched is not None
            assert fetched.name == "Lab approval"
            listed = await engine.list_definitions()
            assert [d.def_id for d in listed] == ["def-1"]
            await session.close()

        asyncio.run(scenario())

    def test_authenticated_route_uses_bridged_session(self, session):
        app = FastAPI()
        app.include_router(workflows_routes.router)

        async def fake_identity():
            return {"id": "u1", "role": "master_admin"}

        def override_db():
            yield session

        app.dependency_overrides[get_current_identity] = fake_identity
        app.dependency_overrides[workflows_routes.get_db] = override_db
        client = TestClient(app)
        response = client.get(
            "/workflows/definitions",
            headers={"Authorization": "Bearer test"},
        )
        assert response.status_code == 200
        assert response.json() == []
