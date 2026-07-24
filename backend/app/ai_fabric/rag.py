from __future__ import annotations

import logging
import math
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app._compat import StrEnum
from app.ai_fabric.base import InferenceRequest
from app.ai_fabric.gateway import AIGateway

logger = logging.getLogger("gula.ai_fabric.rag")


class VectorDBType(StrEnum):
    PGVECTOR = "pgvector"
    QDRANT = "qdrant"
    MILVUS = "milvus"


@dataclass
class Chunk:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    score: float = 0.0


@dataclass
class RetrievedDocument:
    chunk: Chunk
    relevance_score: float = 0.0
    rank: int = 0


@dataclass
class Citation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    text: str = ""
    relevance_score: float = 0.0
    chunk_id: str = ""


class SearchMode(StrEnum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class VectorStore:
    def __init__(self, db_type: VectorDBType = VectorDBType.PGVECTOR, config: dict[str, Any] | None = None) -> None:
        self._db_type = db_type
        self._config = config or {}
        self._dimension: int = self._config.get("dimension", 384)
        self._index_name: str = self._config.get("index_name", "gula_embeddings")
        self._collections: dict[str, list[Chunk]] = {}

    async def upsert(self, collection: str, chunks: list[Chunk]) -> int:
        if collection not in self._collections:
            self._collections[collection] = []
        self._collections[collection].extend(chunks)
        logger.info("Upserted %d chunks into collection %s", len(chunks), collection)
        return len(chunks)

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> list[Chunk]:
        docs = self._collections.get(collection, [])
        scored: list[tuple[Chunk, float]] = []
        for chunk in docs:
            if chunk.embedding:
                score = self._cosine_similarity(query_embedding, chunk.embedding)
                if score >= threshold:
                    scored.append((chunk, score))
            else:
                scored.append((chunk, 0.0))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_k]]

    async def delete_collection(self, collection: str) -> bool:
        return self._collections.pop(collection, None) is not None

    async def list_collections(self) -> list[str]:
        return list(self._collections.keys())

    async def collection_stats(self, collection: str) -> dict[str, Any]:
        docs = self._collections.get(collection, [])
        return {
            "name": collection,
            "chunk_count": len(docs),
            "dimension": self._dimension,
        }

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(av * bv for av, bv in zip(a, b, strict=False))
        na = math.sqrt(sum(av * av for av in a))
        nb = math.sqrt(sum(bv * bv for bv in b))
        if not na or not nb:
            return 0.0
        return dot / (na * nb)


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._docs: list[tuple[str, str]] = []
        self._avg_doc_len: float = 0.0
        self._doc_count: int = 0
        self._term_freqs: list[dict[str, int]] = []
        self._doc_freqs: dict[str, int] = {}

    def index(self, docs: list[Chunk]) -> None:
        self._docs = [(c.id, c.text) for c in docs]
        self._doc_count = len(docs)
        total_len = 0
        self._term_freqs = []
        self._doc_freqs = {}
        for _doc_id, text in self._docs:
            tokens = self._tokenize(text)
            total_len += len(tokens)
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self._term_freqs.append(tf)
            for t in set(tokens):
                self._doc_freqs[t] = self._doc_freqs.get(t, 0) + 1
        self._avg_doc_len = total_len / self._doc_count if self._doc_count else 0.0

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or not self._doc_count:
            return []
        scores: list[float] = []
        for i in range(self._doc_count):
            score = 0.0
            doc_len = sum(self._term_freqs[i].values())
            for qt in query_tokens:
                if qt not in self._term_freqs[i]:
                    continue
                tf = self._term_freqs[i][qt]
                df = self._doc_freqs.get(qt, 0)
                idf = math.log((self._doc_count - df + 0.5) / (df + 0.5) + 1.0)
                numerator = tf * (self._k1 + 1)
                denominator = tf + self._k1 * (1 - self._b + self._b * doc_len / self._avg_doc_len)
                score += idf * numerator / denominator
            scores.append(score)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(i, score) for i, score in ranked if score > 0][:top_k]

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())


class SemanticSearch:
    def __init__(self, gateway: AIGateway, vector_store: VectorStore | None = None) -> None:
        self._gateway = gateway
        self._vector_store = vector_store or VectorStore()
        self._bm25: BM25Index | None = None

    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        mode: SearchMode = SearchMode.HYBRID,
        threshold: float = 0.0,
    ) -> list[RetrievedDocument]:
        query_embedding = await self._embed_query(query)

        if mode == SearchMode.KEYWORD:
            return await self._keyword_search(query, collection, top_k)

        semantic_results = await self._vector_store.search(
            collection, query_embedding, top_k=top_k * 2, threshold=threshold,
        )

        if mode == SearchMode.SEMANTIC:
            return [
                RetrievedDocument(chunk=c, relevance_score=c.score, rank=i)
                for i, c in enumerate(semantic_results)
            ][:top_k]

        keyword_results = await self._keyword_search(query, collection, top_k * 2)
        return self._fuse_results(semantic_results, keyword_results, top_k)

    async def _embed_query(self, query: str) -> list[float]:
        embeddings = self._gateway.embed([query])
        return embeddings[0] if embeddings else [0.0] * 384

    async def _keyword_search(self, query: str, collection: str, top_k: int) -> list[RetrievedDocument]:
        docs = self._vector_store._collections.get(collection, [])
        if not docs:
            return []
        if not self._bm25:
            self._bm25 = BM25Index()
            self._bm25.index(docs)
        results = self._bm25.search(query, top_k=top_k)
        return [
            RetrievedDocument(chunk=docs[i], relevance_score=score, rank=rank)
            for rank, (i, score) in enumerate(results)
        ]

    def _fuse_results(
        self,
        semantic: list[Chunk],
        keyword: list[RetrievedDocument],
        top_k: int,
    ) -> list[RetrievedDocument]:
        seen: set[str] = set()
        fused: list[RetrievedDocument] = []
        for chunk in semantic:
            if chunk.id not in seen:
                seen.add(chunk.id)
                fused.append(RetrievedDocument(chunk=chunk, relevance_score=chunk.score, rank=len(fused)))
        for rd in keyword:
            if rd.chunk.id not in seen:
                seen.add(rd.chunk.id)
                fused.append(rd)
        return fused[:top_k]

    def build_index(self, collection: str) -> None:
        docs = self._vector_store._collections.get(collection, [])
        if docs:
            self._bm25 = BM25Index()
            self._bm25.index(docs)


class CitationEngine:
    def __init__(self, min_relevance: float = 0.3) -> None:
        self._min_relevance = min_relevance

    def generate_citations(
        self,
        documents: list[RetrievedDocument],
        llm_response: str,
    ) -> list[Citation]:
        citations: list[Citation] = []
        for doc in documents:
            if doc.relevance_score < self._min_relevance:
                continue
            citation = Citation(
                source=doc.chunk.source,
                text=doc.chunk.text[:200],
                relevance_score=round(doc.relevance_score, 4),
                chunk_id=doc.chunk.id,
            )
            citations.append(citation)
        return citations

    def format_citations(self, citations: list[Citation], format: str = "text") -> str:
        if format == "json":
            import json
            return json.dumps([{
                "id": c.id,
                "source": c.source,
                "relevance_score": c.relevance_score,
                "text": c.text,
            } for c in citations], ensure_ascii=False)

        lines = []
        for i, c in enumerate(citations, 1):
            lines.append(f"[{i}] {c.source} (relevance: {c.relevance_score:.2f})")
            lines.append(f"    {c.text}")
        return "\n".join(lines)

    def score_coverage(self, citations: list[Citation], num_docs_used: int, total_docs: int) -> float:
        if not total_docs:
            return 0.0
        coverage = num_docs_used / total_docs
        avg_relevance = (
            sum(c.relevance_score for c in citations) / len(citations)
            if citations else 0.0
        )
        return round(coverage * 0.4 + avg_relevance * 0.6, 4)


class ContextBuilder:
    def __init__(self, max_tokens: int = 8192) -> None:
        self._max_tokens = max_tokens

    def build_context(
        self,
        documents: list[RetrievedDocument],
        query: str,
        system_instruction: str = "",
        max_docs: int = 15,
    ) -> str:
        selected = documents[:max_docs]
        parts: list[str] = []
        token_budget = self._max_tokens - self._estimate_tokens(query) - self._estimate_tokens(system_instruction)
        token_budget = max(token_budget, 512)

        for doc in selected:
            doc_text = f"Source: {doc.chunk.source}\n{doc.chunk.text}"
            doc_tokens = self._estimate_tokens(doc_text) + 10
            if token_budget - doc_tokens < 0:
                break
            parts.append(doc_text)
            token_budget -= doc_tokens

        if system_instruction:
            parts.insert(0, system_instruction)

        parts.append(f"User Query: {query}")
        return "\n\n---\n\n".join(parts)

    def build_structured_context(
        self,
        documents: list[RetrievedDocument],
        query: str,
        categories: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        sections: dict[str, list[dict]] = {}
        for doc in documents:
            cat = doc.chunk.metadata.get("category", "general")
            if categories and cat not in categories:
                cat = "general"
            if cat not in sections:
                sections[cat] = []
            sections[cat].append({
                "source": doc.chunk.source,
                "text": doc.chunk.text[:500],
                "score": doc.relevance_score,
            })
        return {
            "query": query,
            "sections": sections,
            "document_count": len(documents),
        }

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4 + 1


class RAGEngine:
    def __init__(
        self,
        gateway: AIGateway,
        vector_store: VectorStore | None = None,
        semantic_search: SemanticSearch | None = None,
        citation_engine: CitationEngine | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self._gateway = gateway
        self._vector_store = vector_store or VectorStore()
        self._semantic_search = semantic_search or SemanticSearch(gateway, self._vector_store)
        self._citation_engine = citation_engine or CitationEngine()
        self._context_builder = context_builder or ContextBuilder()

    async def query(
        self,
        query_text: str,
        collection: str,
        top_k: int = 10,
        search_mode: SearchMode = SearchMode.HYBRID,
        model: str = "gpt-4o-mini",
        system_prompt: str = "",
        include_citations: bool = True,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        start = time.monotonic()
        documents = await self._semantic_search.search(
            query=query_text, collection=collection, top_k=top_k, mode=search_mode,
        )

        if not documents:
            return {
                "answer": "No relevant documents found.",
                "documents": [],
                "citations": [],
                "latency_ms": (time.monotonic() - start) * 1000,
                "document_count": 0,
            }

        context = self._context_builder.build_context(documents, query_text, system_prompt)

        request = InferenceRequest(
            prompt=f"Answer the query based on the provided context.\n\nContext:\n{context}",
            model=model,
            temperature=temperature,
            max_tokens=2048,
            system_prompt=system_prompt or "You are a helpful medical AI assistant. Answer based only on the provided context.",
        )
        response = self._gateway.chat(request)

        citations = []
        if include_citations:
            citations = self._citation_engine.generate_citations(documents, response.text)

        elapsed = (time.monotonic() - start) * 1000
        return {
            "answer": response.text,
            "documents": [
                {
                    "id": d.chunk.id,
                    "source": d.chunk.source,
                    "text": d.chunk.text[:300],
                    "relevance_score": d.relevance_score,
                    "rank": d.rank,
                }
                for d in documents[:5]
            ],
            "citations": [
                {
                    "id": c.id,
                    "source": c.source,
                    "relevance_score": c.relevance_score,
                    "text": c.text,
                }
                for c in citations
            ],
            "model": response.model,
            "latency_ms": round(elapsed, 2),
            "document_count": len(documents),
            "citation_coverage": self._citation_engine.score_coverage(
                citations, len(citations), len(documents),
            ),
        }

    async def index_documents(self, collection: str, chunks: list[Chunk]) -> int:
        count = await self._vector_store.upsert(collection, chunks)
        self._semantic_search.build_index(collection)
        return count
