from __future__ import annotations

import asyncio
import inspect
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.national.task_engine.domain.entities import TaskAuditLog
from app.national.task_engine.infrastructure.repository import (
    CanonicalTaskAuditRepository,
    _default_async_session_factory,
)


def _async_session_mock():
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.__aexit__.return_value = False
    session.commit = AsyncMock()
    return session


class TestWiringRepoint:
    """Order 17 (#9): the no-op SQLAlchemyTaskAuditLogRepository is gone from
    the task_engine infrastructure; the composition root now injects the
    canonical-backed adapter."""

    def test_noop_repo_removed_from_module(self):
        from app.national.task_engine.infrastructure import repository

        assert not hasattr(repository, "SQLAlchemyTaskAuditLogRepository")
        assert hasattr(repository, "CanonicalTaskAuditRepository")

    def test_module_no_longer_matches_audit_gate_signal(self):
        from app.national.task_engine.infrastructure import repository

        source = inspect.getsource(repository)
        signal = re.compile(r"class\s+\w*(?:AuditService|AuditLogger|AuditLogRepository)\b")
        assert not signal.search(source), (
            "audit reimplementation signal still present in task_engine repository.py"
        )

    def test_adapter_is_thin_canonical_delegator(self):
        source = inspect.getsource(CanonicalTaskAuditRepository)
        assert "record_event" in source
        assert "from app.identity.services.audit_service import AuditService" in source

    def test_default_session_factory_is_lazy_callable(self):
        factory = _default_async_session_factory()
        assert callable(factory)


class TestCanonicalTaskAuditRepository:
    """Behavior-additive: the adapter persists audit rows through the canonical
    immutable hash-chained AuditService instead of silently dropping them."""

    def _coro(self, coroutine):
        return asyncio.run(coroutine)

    def _log(self, task_id: str = "task-1", action: str = "CREATED") -> TaskAuditLog:
        return TaskAuditLog(
            id="log-1",
            task_id=task_id,
            action=action,
            actor_id="actor-1",
            previous_status=None,
            new_status="assigned",
            details={"title": "Sample", "priority": "high"},
        )

    def test_save_delegates_to_canonical_record_event(self):
        session = _async_session_mock()

        async def run():
            repo = CanonicalTaskAuditRepository(lambda: session)
            with patch("app.identity.services.audit_service.AuditService") as canonical_cls:
                canonical_cls.return_value.record_event = AsyncMock()
                await repo.save(self._log())
            canonical_cls.assert_called_once_with(session)
            call = canonical_cls.return_value.record_event.await_args
            kwargs = call.kwargs if call.kwargs else call.args[1]
            assert kwargs["action"] == "CREATED"
            assert kwargs["target_type"] == "task"
            assert kwargs["target_id"] == "task-1"
            assert kwargs["actor_id"] == "actor-1"
            assert kwargs["metadata"]["previous_status"] is None
            assert kwargs["metadata"]["new_status"] == "assigned"
            session.commit.assert_awaited_once_with()

        self._coro(run())

    def test_save_returns_log(self):
        session = _async_session_mock()

        async def run():
            repo = CanonicalTaskAuditRepository(lambda: session)
            with patch("app.identity.services.audit_service.AuditService") as canonical_cls:
                canonical_cls.return_value.record_event = AsyncMock()
                return await repo.save(self._log())

        log = self._coro(run())
        assert log.id == "log-1"
        assert log.task_id == "task-1"

    def test_find_by_task_queries_canonical_model(self):
        session = _async_session_mock()
        entry = MagicMock()
        entry.id = "e1"
        entry.action = "CREATED"
        entry.actor_id = "actor-1"
        entry.target_id = "task-1"
        entry.occurred_at = None
        entry.extra_data = {
            "task_audit_log_id": "log-1",
            "previous_status": None,
            "new_status": "assigned",
            "details": {"title": "Sample"},
        }
        result = MagicMock()
        result.scalars.return_value.all.return_value = [entry]
        session.execute = AsyncMock(return_value=result)

        async def run():
            repo = CanonicalTaskAuditRepository(lambda: session)
            return await repo.find_by_task("task-1")

        logs = self._coro(run())
        assert len(logs) == 1
        assert logs[0].id == "log-1"
        assert logs[0].task_id == "task-1"
        assert logs[0].action == "CREATED"
        assert logs[0].new_status == "assigned"
        stmt = session.execute.await_args.args[0]
        rendered = str(stmt)
        assert "niam_audit_entries" in rendered
        assert "target_id" in rendered

    def test_save_fail_closed_when_session_unavailable(self):
        def broken_factory():
            raise RuntimeError("no async DB configured")

        async def run():
            repo = CanonicalTaskAuditRepository(broken_factory)
            await repo.save(self._log())

        with pytest.raises(RuntimeError, match="no async DB"):
            self._coro(run())

    def test_save_is_behavior_additive(self):
        """The old no-op logged nothing; the adapter must invoke canonical."""

        session = _async_session_mock()

        async def run():
            repo = CanonicalTaskAuditRepository(lambda: session)
            with patch("app.identity.services.audit_service.AuditService") as canonical_cls:
                canonical_cls.return_value.record_event = AsyncMock()
                await repo.save(self._log(action="STATUS_CHANGED"))
            return canonical_cls.return_value.record_event.await_count

        count = self._coro(run())
        assert count == 1


class TestCompositionRoot:
    """The task_engine API composition root re-points audit to the canonical
    adapter."""

    def test_routes_wire_canonical_adapter(self):
        from app.national.task_engine.api import routes

        source = inspect.getsource(routes._get_service)
        assert "CanonicalTaskAuditRepository()" in source
        assert "SQLAlchemyTaskAuditLogRepository" not in source

    def test_adapter_constructs_with_injected_factory(self):
        def stub_factory():
            return None

        repo = CanonicalTaskAuditRepository(stub_factory)
        assert repo._session_factory is stub_factory


class TestArchivePreserved:
    def test_archived_noop_preserved_for_reversibility(self):
        archive_path = (
            Path(__file__).resolve().parents[3]
            / "archive"
            / "platform-shared-core"
            / "task_engine_sqlalchemy_audit_log_repository.py"
        )
        assert archive_path.exists()
        content = archive_path.read_text()
        assert "class SQLAlchemyTaskAuditLogRepository" in content
        assert "async def save" in content
        assert "async def find_by_task" in content

    def test_old_class_no_longer_importable_from_canonical_path(self):
        from app.national.task_engine.infrastructure import repository

        assert not hasattr(repository, "SQLAlchemyTaskAuditLogRepository")
