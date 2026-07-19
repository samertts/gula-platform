from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.ai.embeddings import cosine_similarity
from app.ai.vector_store import VectorSearchResult, VectorStore, vector_store
from app.gateways.google_ai import generate_chat

logger = logging.getLogger("gula.ai.rag")


@dataclass
class RAGContext:
    documents: list[VectorSearchResult] = field(default_factory=list)
    query: str = ""
    system_prompt: str = ""
    augmented_prompt: str = ""
    max_tokens: int = 1000

    def format_context(self, max_docs: int = 5) -> str:
        seen = set()
        parts = []
        for doc in self.documents[:max_docs]:
            if doc.text in seen:
                continue
            seen.add(doc.text)
            source = doc.source or doc.content_type
            parts.append(f"[المصدر: {source}] {doc.text}")
        return "\n\n".join(parts)

    def count_tokens(self, text: str) -> int:
        return len(text.split())


class RAGPipeline:

    def __init__(self, vector_store_instance: VectorStore | None = None):
        self.vector_store = vector_store_instance or vector_store
        self._system_template = (
            "أنت مساعد ذكي لمنصة GULA للمختبرات الطبية. "
            "استخدم المعلومات التالية من المصادر الموثوقة للإجابة على سؤال المستخدم. "
            "إذا كانت المعلومات المقدمة لا تحتوي على الإجابة، قل ذلك بوضوح ولا تخترع معلومات. "
            "أرفق المصادر في إجابتك باستخدام تنسيق [المصدر: اسم المصدر]. "
            "كن دقيقاً ومفيداً واحترم الخصوصية الطبية."
        )

    async def retrieve(
        self,
        query: str,
        content_type: str | None = None,
        limit: int = 10,
        threshold: float = 0.3,
        lab_id: int | None = None,
    ) -> list[VectorSearchResult]:
        return await self.vector_store.search(
            query=query,
            content_type=content_type,
            limit=limit,
            threshold=threshold,
            lab_id=lab_id,
        )

    async def augment(
        self,
        query: str,
        documents: list[VectorSearchResult],
        max_docs: int = 5,
    ) -> RAGContext:
        ctx = RAGContext(query=query, documents=documents)

        if not documents:
            ctx.augmented_prompt = (
                f"{self._system_template}\n\n"
                f"لم يتم العثور على معلومات كافية في قاعدة المعرفة للإجابة على السؤال التالي. "
                f"يرجى الإشارة إلى ذلك في ردك.\n\n"
                f"سؤال المستخدم: {query}"
            )
            return ctx

        context_text = ctx.format_context(max_docs=max_docs)
        ctx.augmented_prompt = (
            f"{self._system_template}\n\n"
            f"--- المعلومات المسترجعة ---\n"
            f"{context_text}\n"
            f"--- نهاية المعلومات المسترجعة ---\n\n"
            f"بناءً على المعلومات أعلاه، أجب على السؤال التالي:\n\n"
            f"سؤال المستخدم: {query}"
        )
        return ctx

    async def generate(
        self,
        context: RAGContext,
        provider: str = "gemini",
    ) -> dict[str, Any]:
        if not context.augmented_prompt:
            context = await self.augment(context.query, context.documents)

        try:
            if provider == "gemini":
                response = await generate_chat(context.augmented_prompt, context="rag_query")
            else:
                response = "عذراً، مزود الذكاء الاصطناعي غير متوفر حالياً."
        except Exception as exc:
            logger.error("[RAG] Generation failed: %s", exc)
            response = "عذراً، تعذر إنشاء الرد. يرجى المحاولة لاحقاً."

        citations = self._extract_citations(response, context.documents)
        hallucination_score = self._detect_hallucination(response, context.documents)

        return {
            "response": response,
            "citations": citations,
            "hallucination_score": hallucination_score,
            "document_count": len(context.documents),
            "provider": provider,
        }

    async def query(
        self,
        question: str,
        content_type: str | None = None,
        lab_id: int | None = None,
        max_docs: int = 5,
    ) -> dict[str, Any]:
        documents = await self.retrieve(question, content_type=content_type, lab_id=lab_id)
        context = await self.augment(question, documents, max_docs=max_docs)
        return await self.generate(context)

    def rerank(
        self,
        query: str,
        documents: list[VectorSearchResult],
        top_k: int = 5,
    ) -> list[VectorSearchResult]:
        query_terms = set(query.lower().split())
        scored = []
        for doc in documents:
            semantic = doc.score
            text_lower = doc.text.lower()
            term_overlap = len(query_terms & set(text_lower.split()))
            term_ratio = term_overlap / max(len(query_terms), 1)
            combined = 0.7 * semantic + 0.3 * term_ratio
            scored.append((combined, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        for score, doc in scored:
            doc.score = round(score, 4)
        return [doc for _, doc in scored[:top_k]]

    def _extract_citations(
        self, response: str, documents: list[VectorSearchResult]
    ) -> list[dict[str, Any]]:
        citations = []
        for doc in documents:
            source = doc.source or doc.content_type
            pattern = re.escape(f"[المصدر: {source}]")
            if re.search(pattern, response):
                citations.append({
                    "source": source,
                    "content_type": doc.content_type,
                    "content_id": doc.content_id,
                    "score": doc.score,
                    "text_preview": doc.text[:100],
                })
        return citations

    def _detect_hallucination(
        self, response: str, documents: list[VectorSearchResult]
    ) -> float:
        score = 0.0
        response_lower = response.lower()
        all_text = " ".join(d.text.lower() for d in documents)

        overlap = len(set(response_lower.split()) & set(all_text.split()))
        total = len(response_lower.split())
        if total > 0:
            score = 1.0 - (overlap / total)

        score = round(max(0.0, min(1.0, score)), 4)
        return score


rag = RAGPipeline()
