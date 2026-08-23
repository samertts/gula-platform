from __future__ import annotations

from types import SimpleNamespace
import importlib

from app.ai.vector_store import VectorStore

vector_store_module = importlib.import_module("app.ai.vector_store")


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _DB:
    def __init__(self, rows):
        self.rows = rows
        self.statement = None
        self.params = None

    def execute(self, statement, params=None):
        self.statement = str(statement)
        self.params = params or {}
        return _Result(self.rows)

    def close(self):
        return None


def test_delete_refuses_unscoped_embedding_delete(monkeypatch):
    db = _DB([])
    monkeypatch.setattr(vector_store_module, "get_db", lambda: iter([db]))
    monkeypatch.setattr(VectorStore, "_check_pgvector", lambda self: True)

    assert VectorStore().delete("knowledge", 10) is False
    assert db.statement is None


def test_in_memory_fallback_binds_lab_and_scores_stored_embedding(monkeypatch):
    db = _DB([
        SimpleNamespace(
            id=1,
            content_type="knowledge",
            content_id=10,
            text="glucose",
            metadata={},
            embedding=[1.0, 0.0],
        ),
    ])
    monkeypatch.setattr(vector_store_module, "get_db", lambda: iter([db]))

    results = VectorStore(lab_id=7)._search_in_memory(
        query_embedding=[1.0, 0.0],
        content_type="knowledge",
        limit=5,
        threshold=0.9,
        lab_id=7,
    )

    assert len(results) == 1
    assert results[0].id == 1
    assert results[0].score == 1.0
    assert db.params == {"limit": 5, "lab": 7, "ct": "knowledge"}
    assert "lab_id = :lab" in db.statement
    assert "content_type = :ct" in db.statement
