"""PROGRAM-01 Wave 3 Commit 3.3: regression tests for the canonical PDF provider.

The national document platform PDF endpoint (#46 routes + #47 service) was wired
to the canonical ``shared/pdf`` generator through a thin adapter in the canonical
provider ``app.capabilities.document_management.pdf_generator`` (ADR-033).
The ``def generate_pdf`` signals must be vacated so the architecture gate drops
from 33 findings to 31, and behaviour must be preserved exactly.
"""

from __future__ import annotations

import asyncio
import importlib.util
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.national.document_platform.application.interfaces import PDFGenerator
from app.national.document_platform.application.service import DocumentPlatformService
from app.national.document_platform.domain.entities import Document
from app.national.document_platform.domain.enums import (
    DocumentCategory,
    DocumentFormat,
    DocumentStatus,
)
from app.national.document_platform.exceptions import DocumentValidationError


def await_coro(coro):
    return asyncio.run(coro)


def make_document(document_id: str | None = None) -> Document:
    return Document(
        id=document_id or str(uuid4()),
        filename="report.pdf",
        original_name="lab-report.pdf",
        mime_type="application/pdf",
        format=DocumentFormat.PDF,
        size_bytes=2048,
        version=3,
        category=DocumentCategory.LAB_RESULT,
        status=DocumentStatus.FINAL,
        tags=["lab", "glucose"],
        metadata={"patient_id": "pat-1"},
        created_by="u1",
        created_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
    )


class FakeDocumentRepository:
    def __init__(self, document: Document | None):
        self._document = document

    async def get(self, document_id: str) -> Document | None:
        return self._document


def build_service(pdf_generator, document: Document | None = make_document()) -> DocumentPlatformService:
    return DocumentPlatformService(
        document_repository=FakeDocumentRepository(document),
        version_repository=AsyncMock(),
        signature_repository=AsyncMock(),
        qr_code_repository=AsyncMock(),
        attachment_repository=AsyncMock(),
        retention_rule_repository=AsyncMock(),
        event_bus=AsyncMock(),
        pdf_generator=pdf_generator,
    )


class TestCanonicalPdfPromotion:
    def test_canonical_adapter_import_path(self):
        assert importlib.util.find_spec("app.capabilities.document_management.pdf_generator") is not None
        from app.capabilities.document_management.pdf_generator import SharedPdfGenerator

        assert issubclass(SharedPdfGenerator, PDFGenerator)

    def test_generate_pdf_signals_vacated(self):
        import app.national.document_platform.api.routes as routes
        import app.national.document_platform.application.service as svc

        assert not hasattr(routes, "generate_pdf")
        assert hasattr(routes, "export_document_pdf")
        assert not hasattr(DocumentPlatformService, "generate_pdf")
        assert hasattr(DocumentPlatformService, "export_pdf")

    def test_routes_inject_canonical_adapter(self):
        import app.national.document_platform.api.routes as routes

        generator = routes._pdf_generator()
        assert isinstance(generator, PDFGenerator)

    def test_routes_operation_id_preserved(self):
        import app.national.document_platform.api.routes as routes

        ops = [r for r in routes.router.routes if getattr(r, "path", "").endswith("generate-pdf")]
        assert len(ops) == 1
        assert ops[0].operation_id == "generate_pdf_national_documents__document_id__generate_pdf_post"


class TestSharedPdfGenerator:
    def test_generate_returns_real_pdf_bytes(self):
        from app.capabilities.document_management.pdf_generator import SharedPdfGenerator

        gen = SharedPdfGenerator()
        pdf = await_coro(gen.generate({"id": "d1", "filename": "report.pdf"}))
        assert isinstance(pdf, bytes)
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 500

    def test_generate_sync_with_template_title(self):
        from app.capabilities.document_management.pdf_generator import SharedPdfGenerator

        gen = SharedPdfGenerator()
        pdf = gen._generate_sync(
            {"id": "d1", "status": "final", "created_at": "2026-08-01T12:00:00"},
            template="Contract",
        )
        assert pdf.startswith(b"%PDF")


class TestDocumentPlatformServiceExportPdf:
    def test_export_pdf_delegates_to_generator(self):
        document = make_document("d1")
        generator = AsyncMock()
        generator.generate.return_value = b"%PDF-1.4 fake"
        svc = build_service(generator, document)
        result = await_coro(svc.export_pdf("d1", template="contract"))
        assert result == b"%PDF-1.4 fake"
        generator.generate.assert_awaited_once()
        args = generator.generate.await_args.args
        assert args[0]["id"] == "d1"
        assert args[0]["filename"] == "report.pdf"
        assert generator.generate.await_args.kwargs["template"] == "contract"

    def test_export_pdf_raises_when_generator_missing(self):
        svc = build_service(None)
        with pytest.raises(DocumentValidationError, match="PDF generator not configured"):
            await_coro(svc.export_pdf("d1"))

    def test_export_pdf_wraps_generator_failure(self):
        generator = AsyncMock()
        generator.generate.side_effect = RuntimeError("boom")
        svc = build_service(generator)
        with pytest.raises(DocumentValidationError, match="PDF generation failed"):
            await_coro(svc.export_pdf("d1"))

    def test_export_pdf_document_not_found(self):
        generator = AsyncMock()
        svc = build_service(generator, document=None)
        from app.national.document_platform.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError):
            await_coro(svc.export_pdf("missing"))


class TestDocumentPdfRoute:
    @pytest.fixture
    def client(self):
        from app.national.document_platform.api import routes as document_routes
        from app.security.dependencies import get_current_user
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(document_routes.router)

        generator = AsyncMock()
        generator.generate.return_value = b"%PDF-1.4 live route"
        service = build_service(generator)

        def override_service():
            return service

        def override_user():
            return {"id": 1, "role": "admin"}

        app.dependency_overrides[document_routes._get_service] = override_service
        app.dependency_overrides[get_current_user] = override_user
        return TestClient(app), service

    def test_router_path_and_operation_id(self, client):
        from app.national.document_platform.api import routes as document_routes

        assert document_routes.router.prefix == "/national/documents"
        ops = [r for r in document_routes.router.routes if getattr(r, "path", "").endswith("generate-pdf")]
        assert ops[0].operation_id == "generate_pdf_national_documents__document_id__generate_pdf_post"

    def test_generate_pdf_endpoint_returns_success(self, client):
        test_client, _ = client
        r = test_client.post("/national/documents/d1/generate-pdf", json={"template": "contract"})
        assert r.status_code == 200
        assert r.json() == {"document_id": "d1", "pdf_size_bytes": 19, "generated": True}

    def test_generate_pdf_endpoint_without_body(self, client):
        test_client, _ = client
        r = test_client.post("/national/documents/d1/generate-pdf")
        assert r.status_code == 200
        assert r.json()["generated"] is True
