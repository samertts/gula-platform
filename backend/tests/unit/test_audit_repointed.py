from __future__ import annotations

import asyncio
import importlib
import inspect
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.document_intelligence.application.wiring import (
    CanonicalAuditAdapter,
    _default_async_session_factory,
    build_orchestrator,
)


def _async_session_mock():
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.__aexit__.return_value = False
    session.commit = AsyncMock()
    return session


class TestWiringRepoint:
    """Order 16 (#5): the no-op DefaultAuditService is gone from the doc-intel
    wiring; the composition root now injects the canonical-backed adapter."""

    def test_default_audit_service_removed_from_module(self):
        from app.document_intelligence.application import wiring

        assert not hasattr(wiring, "DefaultAuditService")
        assert hasattr(wiring, "CanonicalAuditAdapter")

    def test_wiring_no_longer_matches_audit_gate_signal(self):
        from app.document_intelligence.application import wiring

        source = inspect.getsource(wiring)
        signal = re.compile(r"class\s+\w*(?:AuditService|AuditLogger|AuditLogRepository)\b")
        assert not signal.search(source), "audit reimplementation signal still present in wiring.py"

    def test_adapter_is_thin_canonical_delegator(self):
        source = inspect.getsource(CanonicalAuditAdapter)
        assert "record_event" in source
        assert "from app.identity.services.audit_service import AuditService" in source

    def test_default_session_factory_is_lazy_callable(self):
        factory = _default_async_session_factory()
        assert callable(factory)


class TestCanonicalAuditAdapter:
    """Behavior-additive: the adapter persists audit rows through the canonical
    immutable hash-chained AuditService instead of silently dropping them."""

    def _coro(self, coroutine):
        return asyncio.run(coroutine)

    def test_log_event_delegates_to_canonical_record_event(self):
        session = _async_session_mock()

        async def run():
            adapter = CanonicalAuditAdapter(lambda: session)
            with patch("app.identity.services.audit_service.AuditService") as canonical_cls:
                canonical_cls.return_value.record_event = AsyncMock()
                await adapter.log_event(
                    "document.ingested",
                    "doc-123",
                    {"filename": "x.pdf", "size": 42},
                )
            canonical_cls.assert_called_once_with(session)
            canonical_cls.return_value.record_event.assert_awaited_once_with(
                action="document.ingested",
                target_type="document",
                target_id="doc-123",
                metadata={"filename": "x.pdf", "size": 42},
            )
            session.commit.assert_awaited_once_with()

        self._coro(run())

    def test_get_document_history_queries_canonical_model(self):
        session = _async_session_mock()
        entry = type(
            "Entry",
            (),
            {"to_dict": lambda self: {"id": "e1", "action": "document.ingested"}},
        )()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [entry]
        session.execute = AsyncMock(return_value=result)

        async def run():
            adapter = CanonicalAuditAdapter(lambda: session)
            return await adapter.get_document_history("doc-123")

        history = self._coro(run())
        assert history == [{"id": "e1", "action": "document.ingested"}]
        session.execute.assert_awaited_once()
        stmt = session.execute.await_args.args[0]
        rendered = str(stmt)
        assert "niam_audit_entries" in rendered
        assert "target_id" in rendered

    def test_log_event_fail_closed_when_session_unavailable(self):
        def broken_factory():
            raise RuntimeError("no async DB configured")

        async def run():
            adapter = CanonicalAuditAdapter(broken_factory)
            await adapter.log_event("document.ingested", "doc-123", {})

        with pytest.raises(RuntimeError, match="no async DB"):
            self._coro(run())

    def test_log_event_is_behavior_additive(self):
        """The old no-op logged nothing; the adapter must invoke canonical."""

        session = _async_session_mock()

        async def run():
            adapter = CanonicalAuditAdapter(lambda: session)
            with patch("app.identity.services.audit_service.AuditService") as canonical_cls:
                canonical_cls.return_value.record_event = AsyncMock()
                await adapter.log_event("workflow.started", "doc-9", {})
            return canonical_cls.return_value.record_event.await_count

        count = self._coro(run())
        assert count == 1


class TestBuildOrchestrator:
    """The composition root re-points audit to the canonical adapter. Full
    build_orchestrator() construction is blocked by a pre-existing dormant
    defect (DefaultLayoutDetector is missing 3 abstract methods from
    LayoutDetector — tracked, out of scope for the audit re-point), so the
    wiring is verified at source level."""

    def test_build_orchestrator_wires_canonical_adapter(self):
        from app.document_intelligence.application import wiring

        source = inspect.getsource(wiring.build_orchestrator)
        assert (
            "audit = CanonicalAuditAdapter(audit_session_factory or _default_async_session_factory())"
            in source
        )
        assert "DefaultAuditService" not in source

    def test_build_orchestrator_accepts_audit_session_factory_param(self):
        signature = inspect.signature(build_orchestrator)
        assert "audit_session_factory" in signature.parameters
        assert signature.parameters["audit_session_factory"].default is None

    def test_adapter_constructs_with_injected_factory(self):
        def stub_factory():
            return None

        adapter = CanonicalAuditAdapter(stub_factory)
        assert adapter._session_factory is stub_factory


class TestArchivePreserved:
    def test_archived_noop_preserved_for_reversibility(self):
        archive_path = (
            Path(__file__).resolve().parents[3]
            / "archive"
            / "platform-shared-core"
            / "document_intelligence_default_audit_service.py"
        )
        assert archive_path.exists()
        content = archive_path.read_text()
        assert "class DefaultAuditService" in content
        assert "log_event" in content

    def test_old_class_no_longer_importable_from_canonical_path(self):
        module = importlib.import_module("app.document_intelligence.application.wiring")
        assert not hasattr(module, "DefaultAuditService")
