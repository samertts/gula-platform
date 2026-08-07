"""PROGRAM-01 Wave 3 Commit 3.2: regression tests for the canonical search provider.

The search capability (#35 DefaultSearchService + #36 InfrastructureSemanticSearchService)
was promoted from the document_intelligence bounded context into the canonical
provider ``app.capabilities.search_service`` (ADR-033). The old namespace must be
fully vacated and the canonical provider must preserve behaviour exactly.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.capabilities.search_service import (
    DefaultSearchIndexer,
    DefaultSearchService,
    IndexingError,
    InfrastructureSemanticSearchService,
    SearchableDocument,
    SearchError,
    composition,
)
from app.capabilities.search_service import routes as search_routes
from fastapi import FastAPI
from fastapi.testclient import TestClient


@dataclass
class FakeDoc:
    id: object
    filename: str
    mime_type: str
    page_count: int
    created_at: datetime
    metadata: dict
    tags: list[str]


@dataclass
class FakeEntity:
    entity_type: object
    value: str
    confidence: float


def make_doc(text: str = "diabetes glucose report", patient_id: str = "pat-1"):
    return FakeDoc(
        id=uuid4(),
        filename="report.pdf",
        mime_type="application/pdf",
        page_count=2,
        created_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        metadata={"patient_id": patient_id},
        tags=["lab"],
    )


def await_coro(coro):
    import asyncio

    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def reset_singletons():
    composition._indexer = None
    composition._search_service = None
    yield
    composition._indexer = None
    composition._search_service = None


class TestCanonicalPromotion:
    def test_canonical_import_paths(self):
        assert importlib.util.find_spec("app.capabilities.search_service") is not None
        assert importlib.util.find_spec("app.capabilities.search_service.indexer") is not None
        assert importlib.util.find_spec("app.capabilities.search_service.search") is not None
        assert importlib.util.find_spec("app.capabilities.search_service.semantic") is not None
        assert importlib.util.find_spec("app.capabilities.search_service.composition") is not None
        assert importlib.util.find_spec("app.capabilities.search_service.routes") is not None

    def test_old_namespace_vacated(self):
        import app.document_intelligence.application.service as svc
        import app.document_intelligence.application.wiring as wiring
        import app.document_intelligence.infrastructure.services as infra

        assert not hasattr(svc, "DefaultSearchService")
        assert not hasattr(wiring, "DefaultSearchIndexer")
        assert not hasattr(infra, "InfrastructureSemanticSearchService")

    def test_wiring_uses_canonical_provider(self):
        import pathlib

        import app.document_intelligence.application.wiring as wiring

        src = pathlib.Path(wiring.__file__).read_text(encoding="utf-8")
        assert "from app.capabilities.search_service.indexer import DefaultSearchIndexer" in src
        assert "from app.capabilities.search_service.search import DefaultSearchService" in src
        assert "from app.capabilities.search_service.semantic import InfrastructureSemanticSearchService" in src

    def test_canonical_exports(self):
        assert isinstance(DefaultSearchIndexer, type)
        assert isinstance(DefaultSearchService, type)
        assert isinstance(InfrastructureSemanticSearchService, type)
        assert issubclass(SearchError, Exception)
        assert issubclass(IndexingError, Exception)

    def test_capability_scaffold_intact(self):
        from app.capabilities.search_service.capability import Search_serviceCapability
        from app.capabilities.search_service.contract import (
            Search_serviceInput,
            Search_serviceOutput,
        )

        assert Search_serviceCapability is not None
        assert Search_serviceInput is not None
        assert Search_serviceOutput is not None

    def test_queries_and_commands_scaffold_intact(self):
        from app.capabilities.search_service.commands import (
            Delete_indexCommand,
            Index_documentCommand,
            ReindexCommand,
        )
        from app.capabilities.search_service.queries import (
            Get_search_statsQuery,
            SearchQuery,
            SuggestQuery,
        )

        for cls in (
            SearchQuery,
            SuggestQuery,
            Get_search_statsQuery,
            Index_documentCommand,
            ReindexCommand,
            Delete_indexCommand,
        ):
            assert isinstance(cls, type)


class TestDefaultSearchIndexer:
    def test_index_document_returns_id(self):
        indexer = DefaultSearchIndexer()
        doc = make_doc()
        assert await_coro(indexer.index_document(doc, "glucose", [])) == str(doc.id)

    def test_index_document_truncates_text_and_entities(self):
        indexer = DefaultSearchIndexer()
        doc = make_doc()
        long_text = "a" * 12000
        entities = [FakeEntity("lab", f"v{i}", 1.0) for i in range(80)]
        await_coro(indexer.index_document(doc, long_text, entities))
        entry = await_coro(indexer.get(doc.id))
        assert len(entry["text"]) == 10000
        assert len(entry["entities"]) == 50

    def test_get_returns_entry(self):
        indexer = DefaultSearchIndexer()
        doc = make_doc()
        await_coro(indexer.index_document(doc, "glucose", []))
        entry = await_coro(indexer.get(doc.id))
        assert entry is not None
        assert entry["document_id"] == str(doc.id)
        assert entry["filename"] == "report.pdf"
        assert entry["metadata"]["patient_id"] == "pat-1"

    def test_get_missing_returns_none(self):
        indexer = DefaultSearchIndexer()
        assert await_coro(indexer.get(uuid4())) is None

    def test_search_contains_match_case_insensitive(self):
        indexer = DefaultSearchIndexer()
        doc = make_doc()
        await_coro(indexer.index_document(doc, "DIABETES Glucose report", []))
        results = await_coro(indexer.search("diabetes"))
        assert len(results) == 1
        results = await_coro(indexer.search("glucose"))
        assert len(results) == 1

    def test_search_filename_match(self):
        indexer = DefaultSearchIndexer()
        doc = make_doc()
        await_coro(indexer.index_document(doc, "x", []))
        results = await_coro(indexer.search("report.pdf"))
        assert len(results) == 1

    def test_search_no_match(self):
        indexer = DefaultSearchIndexer()
        await_coro(indexer.index_document(make_doc(), "glucose", []))
        assert await_coro(indexer.search("zzz")) == []

    def test_search_patient_id_filter(self):
        indexer = DefaultSearchIndexer()
        doc = make_doc()
        await_coro(indexer.index_document(doc, "glucose", []))
        results = await_coro(indexer.search("glucose", {"patient_id": "pat-1"}))
        assert len(results) == 1
        results = await_coro(indexer.search("glucose", {"patient_id": "other"}))
        assert len(results) == 0

    def test_search_limit_clamped(self):
        indexer = DefaultSearchIndexer()
        for i in range(5):
            await_coro(indexer.index_document(make_doc(f"doc {i}", f"pat-{i}"), "glucose", []))
        assert len(await_coro(indexer.search("glucose"))) == 5
        assert len(await_coro(indexer.search("glucose", {"limit": 2}))) == 2

    def test_search_sorts_by_created_at_desc(self):
        indexer = DefaultSearchIndexer()
        old = FakeDoc(
            id=uuid4(), filename="old.pdf", mime_type="pdf", page_count=1,
            created_at=datetime(2026, 1, 1, tzinfo=UTC), metadata={}, tags=[],
        )
        new = FakeDoc(
            id=uuid4(), filename="new.pdf", mime_type="pdf", page_count=1,
            created_at=datetime(2026, 8, 1, tzinfo=UTC), metadata={}, tags=[],
        )
        await_coro(indexer.index_document(new, "glucose", []))
        await_coro(indexer.index_document(old, "glucose", []))
        results = await_coro(indexer.search("glucose"))
        assert [r["filename"] for r in results] == ["new.pdf", "old.pdf"]

    def test_hybrid_and_semantic_delegate(self):
        indexer = DefaultSearchIndexer()
        await_coro(indexer.index_document(make_doc(), "glucose", []))
        assert len(await_coro(indexer.hybrid_search("glucose"))) == 1
        assert len(await_coro(indexer.semantic_search("glucose", limit=10))) == 1

    def test_delete_index(self):
        indexer = DefaultSearchIndexer()
        doc = make_doc()
        await_coro(indexer.index_document(doc, "glucose", []))
        await_coro(indexer.delete_index(doc.id))
        assert await_coro(indexer.get(doc.id)) is None
        assert await_coro(indexer.search("glucose")) == []

    def test_rebuild_index(self):
        indexer = DefaultSearchIndexer()
        await_coro(indexer.index_document(make_doc(), "glucose", []))
        await_coro(indexer.rebuild_index())
        assert await_coro(indexer.search("glucose")) == []


class TestDefaultSearchService:
    def test_index_document_delegates(self):
        indexer = AsyncMock()
        svc = DefaultSearchService(indexer)
        await_coro(svc.index_document("d", "text", []))
        indexer.index_document.assert_awaited_once_with("d", "text", [])

    def test_index_document_wraps_error(self):
        indexer = AsyncMock()
        indexer.index_document.side_effect = RuntimeError("boom")
        svc = DefaultSearchService(indexer)
        with pytest.raises(IndexingError, match="Search indexing failed"):
            await_coro(svc.index_document("d", "text", []))

    def test_search_delegates(self):
        indexer = AsyncMock()
        indexer.search.return_value = ["a"]
        svc = DefaultSearchService(indexer)
        assert await_coro(svc.search("q", {"limit": 10})) == ["a"]
        indexer.search.assert_awaited_once_with("q", {"limit": 10})

    def test_search_wraps_error(self):
        indexer = AsyncMock()
        indexer.search.side_effect = RuntimeError("boom")
        svc = DefaultSearchService(indexer)
        with pytest.raises(SearchError, match="Search failed"):
            await_coro(svc.search("q"))

    def test_advanced_search_all_filters(self):
        indexer = AsyncMock()
        indexer.search.return_value = []
        svc = DefaultSearchService(indexer)
        await_coro(svc.advanced_search(
            "q",
            document_type="category-x",
            date_from="2026-01-01",
            date_to="2026-12-31",
            patient_id="pat-1",
            doctor_name="Dr Ali",
            lab_name="Lab One",
            limit=25,
        ))
        args = indexer.search.await_args.args
        assert args[1] == {
            "limit": 25,
            "category": "category-x",
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "patient_id": "pat-1",
            "doctor_name": "Dr Ali",
            "lab_name": "Lab One",
        }

    def test_advanced_search_default_limit(self):
        indexer = AsyncMock()
        indexer.search.return_value = []
        svc = DefaultSearchService(indexer)
        await_coro(svc.advanced_search("q"))
        assert indexer.search.await_args.args[1] == {"limit": 50}

    def test_advanced_search_wraps_error(self):
        indexer = AsyncMock()
        indexer.search.side_effect = RuntimeError("boom")
        svc = DefaultSearchService(indexer)
        with pytest.raises(SearchError, match="Advanced search failed"):
            await_coro(svc.advanced_search("q"))


class TestInfrastructureSemanticSearchService:
    def make_mock_repo(self, docs=None):
        repo = AsyncMock()
        repo.search.return_value = (docs or [], 0)
        return repo

    def test_search(self):
        doc = make_doc()
        repo = self.make_mock_repo([doc])
        svc = InfrastructureSemanticSearchService(repo)
        query = MagicQuery("diabetes", limit=10)
        results = await_coro(svc.search(query))
        assert len(results) == 1
        assert results[0].document_id == doc.id
        assert results[0].score == 1.0
        assert results[0].text_snippet == "report.pdf"
        repo.search.assert_awaited_once_with("diabetes", limit=10)

    def test_hybrid_search(self):
        doc = make_doc()
        repo = self.make_mock_repo([doc])
        svc = InfrastructureSemanticSearchService(repo)
        results = await_coro(svc.hybrid_search("glucose"))
        assert len(results) == 1
        repo.search.assert_awaited_once_with("glucose", limit=20)

    def test_arabic_and_natural_language_delegate(self):
        doc = make_doc()
        repo = self.make_mock_repo([doc])
        svc = InfrastructureSemanticSearchService(repo)
        assert len(await_coro(svc.arabic_search("سكر"))) == 1
        assert len(await_coro(svc.natural_language_query("مستوى السكر"))) == 1

    def test_similar_documents_empty(self):
        svc = InfrastructureSemanticSearchService(self.make_mock_repo())
        assert await_coro(svc.similar_documents(uuid4())) == []

    def test_search_by_entity_empty(self):
        svc = InfrastructureSemanticSearchService(self.make_mock_repo())
        assert await_coro(svc.search_by_entity("lab", "x")) == []

    def test_suggest_queries(self):
        svc = InfrastructureSemanticSearchService(self.make_mock_repo())
        assert await_coro(svc.suggest_queries("glu")) == ["glu_1", "glu_2"]


class TestComposition:
    def test_get_search_indexer_singleton(self):
        assert composition.get_search_indexer() is composition.get_search_indexer()
        assert isinstance(composition.get_search_indexer(), DefaultSearchIndexer)

    def test_get_search_service_singleton(self):
        svc = composition.get_search_service()
        assert svc is composition.get_search_service()
        assert isinstance(svc, DefaultSearchService)
        assert isinstance(svc._indexer, DefaultSearchIndexer)

    def test_service_shares_indexer(self):
        assert composition.get_search_service()._indexer is composition.get_search_indexer()


class TestSearchServiceRoutes:
    @pytest.fixture
    def client(self):
        from app.security.dependencies import get_current_user

        app = FastAPI()
        app.include_router(search_routes.router)
        app.dependency_overrides[get_current_user] = lambda: {"id": "u1", "role": "admin"}
        return TestClient(app)

    def test_router_prefix_and_tags(self):
        assert search_routes.router.prefix == "/search-service"
        assert search_routes.router.tags == ["Search Service"]

    def test_list_empty(self, client):
        r = client.get("/search-service/")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_crud_round_trip(self, client):
        payload = {
            "filename": "report.pdf",
            "mime_type": "application/pdf",
            "page_count": 2,
            "text": "diabetes glucose results",
            "metadata": {"patient_id": "pat-1"},
        }
        created = client.post("/search-service/", json=payload)
        assert created.status_code == 200
        doc_id = created.json()["id"]

        fetched = client.get(f"/search-service/{doc_id}")
        assert fetched.status_code == 200
        assert fetched.json()["filename"] == "report.pdf"

        listing = client.get("/search-service/")
        assert listing.status_code == 200
        assert listing.json()["total"] == 1

        updated = client.put(f"/search-service/{doc_id}", json={**payload, "filename": "v2.pdf"})
        assert updated.status_code == 200
        assert updated.json()["id"] == doc_id
        assert client.get(f"/search-service/{doc_id}").json()["filename"] == "v2.pdf"

        deleted = client.delete(f"/search-service/{doc_id}")
        assert deleted.status_code == 200
        assert client.get(f"/search-service/{doc_id}").json()["id"] == doc_id
        assert client.get("/search-service/").json()["total"] == 0

    def test_get_missing_returns_id_only(self, client):
        r = client.get("/search-service/nope")
        assert r.status_code == 200
        assert r.json() == {"id": "nope"}

    def test_created_at_passthrough(self, client):
        payload = {
            "filename": "f.pdf",
            "created_at": "2026-08-01T00:00:00",
            "text": "content",
        }
        created = client.post("/search-service/", json=payload)
        doc_id = created.json()["id"]
        entry = client.get(f"/search-service/{doc_id}").json()
        assert entry["created_at"] == "2026-08-01T00:00:00"


@dataclass
class MagicQuery:
    query_text: str = ""
    query_vector: list[float] | None = None
    category_filter: list = None
    entity_filter: dict | None = None
    date_range: tuple | None = None
    confidentiality_filter: list = None
    limit: int = 20
    offset: int = 0
    hybrid_search: bool = True
    arabic_boost: bool = True
    metadata: dict | None = None
