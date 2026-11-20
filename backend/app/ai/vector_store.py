from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

from app.ai.embeddings import cosine_similarity, embed_text
from app.database import get_db

logger = logging.getLogger("gula.ai.vector_store")

_ENABLE_PGVECTOR = os.getenv("ENABLE_PGVECTOR", "false").lower() == "true"


@dataclass
class VectorSearchResult:
    id: int
    content_type: str
    content_id: int | None
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""


class VectorStore:

    def __init__(self, lab_id: int | None = None):
        self.lab_id = lab_id
        self._pgvector_available: bool | None = None

    def _check_pgvector(self) -> bool:
        if self._pgvector_available is not None:
            return self._pgvector_available
        if not _ENABLE_PGVECTOR:
            self._pgvector_available = False
            return False
        try:
            db = next(get_db())
            result = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
            self._pgvector_available = result is not None
            db.close()
        except Exception:
            self._pgvector_available = False
        return self._pgvector_available

    async def index_text(
        self,
        text: str,
        content_type: str,
        content_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        lab_id: int | None = None,
    ) -> dict[str, Any]:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        if not text.strip():
            return {"id": None, "content_hash": content_hash, "warning": "empty text"}

        embedding = await embed_text(text, task_type="RETRIEVAL_DOCUMENT")
        lab = lab_id or self.lab_id

        if self._check_pgvector():
            return self._index_pgvector(text, embedding, content_type, content_id, metadata or {}, lab, content_hash)

        return {
            "id": None,
            "content_hash": content_hash,
            "embedding_dim": len(embedding),
            "note": "pgvector not available; stored as metadata only",
        }

    def _index_pgvector(self, text, embedding, content_type, content_id, metadata, lab_id, content_hash):
        db = next(get_db())
        try:
            existing = db.execute(
                text("SELECT id FROM ai_embeddings WHERE content_hash = :ch AND lab_id = :lab"),
                {"ch": content_hash, "lab": lab_id},
            ).fetchone()
            vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
            meta_json = json.dumps(metadata, ensure_ascii=False)
            if existing:
                db.execute(
                    text("UPDATE ai_embeddings SET embedding = :vec::vector, text = :txt, metadata = :meta::jsonb, model = :model WHERE id = :id"),
                    {"vec": vec_str, "txt": text, "meta": meta_json, "model": "gemini-embedding-exp-03-07", "id": existing[0]},
                )
                record_id = existing[0]
            else:
                result = db.execute(
                    text("INSERT INTO ai_embeddings (lab_id, content_type, content_id, content_hash, text, embedding, model, dimensions, metadata) VALUES (:lab, :ct, :cid, :ch, :txt, :vec::vector, :model, :dims, :meta::jsonb) RETURNING id"),
                    {"lab": lab_id, "ct": content_type, "cid": content_id, "ch": content_hash, "txt": text, "vec": vec_str, "model": "gemini-embedding-exp-03-07", "dims": len(embedding), "meta": meta_json},
                )
                record_id = result.fetchone()[0]
            db.commit()
            return {"id": record_id, "content_hash": content_hash, "dimensions": len(embedding)}
        except Exception as exc:
            db.rollback()
            logger.error("[VectorStore] pgvector index failed: %s", exc)
            return {"id": None, "content_hash": content_hash, "error": str(exc)}
        finally:
            db.close()

    async def search(
        self,
        query: str,
        content_type: str | None = None,
        limit: int = 10,
        threshold: float = 0.0,
        lab_id: int | None = None,
    ) -> list[VectorSearchResult]:
        query_embedding = await embed_text(query, task_type="RETRIEVAL_QUERY")

        if self._check_pgvector():
            return self._search_pgvector(query_embedding, content_type, limit, threshold, lab_id)

        return self._search_in_memory(query_embedding, content_type, limit, threshold, lab_id)

    def _search_pgvector(self, query_embedding, content_type, limit, threshold, lab_id):
        db = next(get_db())
        try:
            vec_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
            params: dict[str, Any] = {"vec": vec_str, "limit": limit}
            lab = lab_id if lab_id is not None else self.lab_id
            if lab is not None:
                params["lab"] = lab
            if content_type:
                params["ct"] = content_type
            if lab is not None and content_type:
                sql = text("SELECT e.id, e.content_type, e.content_id, e.text, e.metadata, 1 - (e.embedding <=> :vec::vector) AS score FROM ai_embeddings e WHERE e.lab_id = :lab AND e.content_type = :ct ORDER BY score DESC LIMIT :limit")
            elif lab is not None:
                sql = text("SELECT e.id, e.content_type, e.content_id, e.text, e.metadata, 1 - (e.embedding <=> :vec::vector) AS score FROM ai_embeddings e WHERE e.lab_id = :lab ORDER BY score DESC LIMIT :limit")
            elif content_type:
                sql = text("SELECT e.id, e.content_type, e.content_id, e.text, e.metadata, 1 - (e.embedding <=> :vec::vector) AS score FROM ai_embeddings e WHERE e.content_type = :ct ORDER BY score DESC LIMIT :limit")
            else:
                sql = text("SELECT e.id, e.content_type, e.content_id, e.text, e.metadata, 1 - (e.embedding <=> :vec::vector) AS score FROM ai_embeddings e ORDER BY score DESC LIMIT :limit")
            rows = db.execute(sql, params).fetchall()
            results = []
            for row in rows:
                score = float(row.score)
                if score < threshold:
                    continue
                meta = row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata or "{}")
                results.append(VectorSearchResult(
                    id=row.id, content_type=row.content_type, content_id=row.content_id,
                    text=row.text, score=round(score, 4), metadata=meta,
                ))
            return results
        except Exception as exc:
            logger.error("[VectorStore] pgvector search failed: %s", exc)
            return []
        finally:
            db.close()

    def _search_in_memory(self, query_embedding, content_type, limit, threshold, lab_id):
        db = next(get_db())
        try:
            conditions = []
            params: dict[str, Any] = {"limit": limit}
            lab = lab_id if lab_id is not None else self.lab_id
            if lab is not None:
                conditions.append("lab_id = :lab")
                params["lab"] = lab
            if content_type:
                conditions.append("content_type = :ct")
                params["ct"] = content_type
            where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
            rows = db.execute(
                text(
                    "SELECT id, content_type, content_id, text, metadata, embedding "
                    f"FROM ai_embeddings{where} LIMIT :limit"
                ),
                params,
            ).fetchall()
            scored = []
            for row in rows:
                embedding = row.embedding
                if isinstance(embedding, str):
                    try:
                        embedding = json.loads(embedding)
                    except json.JSONDecodeError:
                        embedding = [float(value) for value in embedding.strip("[]").split(",") if value.strip()]
                if not embedding:
                    continue
                score = cosine_similarity(query_embedding, embedding)
                if score >= threshold:
                    scored.append((score, row))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = []
            for score, row in scored[:limit]:
                meta = row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata or "{}")
                results.append(VectorSearchResult(
                    id=row.id, content_type=row.content_type, content_id=row.content_id,
                    text=row.text, score=round(score, 4), metadata=meta,
                ))
            return results
        except Exception as exc:
            logger.error("[VectorStore] fallback search failed: %s", exc)
            return []
        finally:
            db.close()

    def delete(
        self,
        content_type: str,
        content_id: int,
        lab_id: int | None = None,
    ) -> bool:
        if self._check_pgvector():
            db = next(get_db())
            try:
                lab = lab_id if lab_id is not None else self.lab_id
                if lab is None:
                    logger.error("[VectorStore] refusing unscoped embedding delete")
                    return False
                conditions = ["content_type = :ct", "content_id = :cid", "lab_id = :lab"]
                params: dict[str, Any] = {"ct": content_type, "cid": content_id, "lab": lab}
                db.execute(
                    text(f"DELETE FROM ai_embeddings WHERE {' AND '.join(conditions)}"),
                    params,
                )
                db.commit()
                return True
            except Exception as exc:
                db.rollback()
                logger.error("[VectorStore] delete failed: %s", exc)
                return False
            finally:
                db.close()
        return True

    def search_by_metadata(self, metadata_filter: dict[str, Any], limit: int = 50) -> list[VectorSearchResult]:
        db = next(get_db())
        try:
            params: dict[str, Any] = {"filter_json": json.dumps(metadata_filter), "limit": limit}
            if self.lab_id is not None:
                params["lab"] = self.lab_id
                sql = text("SELECT id, content_type, content_id, text, metadata FROM ai_embeddings WHERE metadata @> :filter_json::jsonb AND lab_id = :lab LIMIT :limit")
            else:
                sql = text("SELECT id, content_type, content_id, text, metadata FROM ai_embeddings WHERE metadata @> :filter_json::jsonb LIMIT :limit")
            rows = db.execute(sql, params).fetchall()
            return [
                VectorSearchResult(
                    id=row.id, content_type=row.content_type, content_id=row.content_id,
                    text=row.text, score=1.0,
                    metadata=row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata or "{}"),
                )
                for row in rows
            ]
        except Exception as exc:
            logger.error("[VectorStore] metadata search failed: %s", exc)
            return []
        finally:
            db.close()


vector_store = VectorStore()
