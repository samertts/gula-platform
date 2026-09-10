from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from app.database import get_db

logger = logging.getLogger("gula.ai.governance")


@dataclass
class ModelRegistryEntry:
    name: str
    provider: str
    model_type: str
    version: str
    capabilities: list[str]
    config: dict[str, Any]
    is_active: bool = True
    max_tokens: int | None = None
    cost_per_1k_input: float | None = None
    cost_per_1k_output: float | None = None


@dataclass
class EvaluationResult:
    id: str
    prompt: str
    response: str
    score: float | None
    metrics: dict[str, Any]
    model: str
    duration_ms: float


class ModelRegistry:

    def __init__(self, *, sync: bool = False):
        """Build the in-memory registry.

        ``sync`` is opt-in and defaults to False because this class is
        constructed at module scope in five places, so seeding from the
        constructor made *importing* ``app.ai`` write to whatever DATABASE_URL
        happened to name. Import is not initialisation. Callers that want the
        row in ``ai_model_registry`` ask for it explicitly. Recorded as NR-019.
        """
        self._models: dict[str, ModelRegistryEntry] = {}
        self._load_defaults(sync=sync)

    def sync_to_db(self) -> None:
        """Persist the default registry. The explicit form of the old import-time write."""
        self._sync_to_db(list(self._models.values()))

    def _load_defaults(self, *, sync: bool = False) -> None:
        defaults = [
            ModelRegistryEntry(name="gemini-2.0-flash", provider="gemini", model_type="chat", version="2.0", capabilities=["chat", "clinical_interpretation", "arabic", "arabic_english"], config={"temperature": 0.5, "max_tokens": 600, "safety": True}, is_active=True, max_tokens=8192),
            ModelRegistryEntry(name="gemini-2.0-flash-thinking", provider="gemini", model_type="reasoning", version="2.0", capabilities=["reasoning", "analysis", "complex_queries"], config={"temperature": 0.3, "max_tokens": 1000}, is_active=True, max_tokens=8192),
            ModelRegistryEntry(name="text-embedding-004", provider="gemini", model_type="embedding", version="1.0", capabilities=["embedding", "semantic_search"], config={"dimensions": 768}, is_active=True, max_tokens=2048),
            ModelRegistryEntry(name="llama3.2:3b", provider="ollama", model_type="chat", version="3.2", capabilities=["chat", "clinical_interpretation", "local"], config={"temperature": 0.3, "num_predict": 550}, is_active=True, max_tokens=4096),
            ModelRegistryEntry(name="llama-3.1-8b-instant", provider="groq", model_type="chat", version="3.1", capabilities=["chat", "fast_inference"], config={"temperature": 0.3, "max_tokens": 500}, is_active=True, max_tokens=8192),
        ]
        for m in defaults:
            self._models[m.name] = m
        if sync:
            self._sync_to_db(defaults)

    def _sync_to_db(self, entries: list[ModelRegistryEntry]) -> None:
        try:
            db = next(get_db())
        except Exception:
            return
        try:
            for m in entries:
                existing = db.execute(text("SELECT id FROM ai_model_registry WHERE name = :name"), {"name": m.name}).fetchone()
                config_json = json.dumps(m.config, ensure_ascii=False)
                caps_json = json.dumps(m.capabilities, ensure_ascii=False)
                if existing:
                    db.execute(text("UPDATE ai_model_registry SET provider=:p, model_type=:mt, version=:v, capabilities=CAST(:caps AS jsonb), config=CAST(:cfg AS jsonb), is_active=:active, max_tokens=:mtok, cost_per_1k_input=:cpi, cost_per_1k_output=:cpo WHERE name=:name"),
                               {"name": m.name, "p": m.provider, "mt": m.model_type, "v": m.version, "caps": caps_json, "cfg": config_json, "active": 1 if m.is_active else 0, "mtok": m.max_tokens, "cpi": m.cost_per_1k_input, "cpo": m.cost_per_1k_output})
                else:
                    db.execute(text("INSERT INTO ai_model_registry (name, provider, model_type, version, capabilities, config, is_active, max_tokens, cost_per_1k_input, cost_per_1k_output) VALUES (:name, :p, :mt, :v, CAST(:caps AS jsonb), CAST(:cfg AS jsonb), :active, :mtok, :cpi, :cpo)"),
                               {"name": m.name, "p": m.provider, "mt": m.model_type, "v": m.version, "caps": caps_json, "cfg": config_json, "active": 1 if m.is_active else 0, "mtok": m.max_tokens, "cpi": m.cost_per_1k_input, "cpo": m.cost_per_1k_output})
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("[Governance] DB sync failed: %s", exc)
        finally:
            db.close()

    def list_models(self, model_type: str | None = None, active_only: bool = True) -> list[dict[str, Any]]:
        models = list(self._models.values())
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        if active_only:
            models = [m for m in models if m.is_active]
        return [
            {"name": m.name, "provider": m.provider, "type": m.model_type, "version": m.version, "capabilities": m.capabilities, "max_tokens": m.max_tokens}
            for m in models
        ]

    def get_model(self, name: str) -> ModelRegistryEntry | None:
        return self._models.get(name)

    def register_model(self, entry: ModelRegistryEntry) -> None:
        self._models[entry.name] = entry
        self._sync_to_db([entry])

    def deactivate_model(self, name: str) -> bool:
        if name in self._models:
            self._models[name].is_active = False
            return True
        return False


model_registry = ModelRegistry()


class PromptManager:

    def __init__(self):
        self._prompts: dict[str, dict[str, Any]] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        self._prompts["clinical_interpretation"] = {
            "version": "2.0",
            "content": "أنت مساعد توعوي طبي. مهمتك شرح نتائج التحاليل للمريض بأسلوب بسيط ومفهوم. لا تُشخّص أمراضاً ولا تصف أدوية ولا توصي بعلاجات بأي شكل.",
            "variables": ["results", "patient_context"],
            "max_tokens": 500,
        }
        self._prompts["agent_planning"] = {
            "version": "1.0",
            "content": "قم بتحديد الأدوات المطلوبة لتنفيذ مهمة المستخدم. اختر من الأدوات المتاحة فقط.",
            "variables": ["task", "tools"],
            "max_tokens": 300,
        }
        self._prompts["rag_query"] = {
            "version": "1.0",
            "content": "استخدم المعلومات المسترجعة من قاعدة المعرفة للإجابة. استشهد بالمصادر. لا تخترع معلومات.\nالسياق: {{context}}\nالسؤال: {{question}}",
            "variables": ["context", "question"],
            "max_tokens": 1000,
        }
        self._prompts["arabic_only"] = {
            "version": "1.0",
            "content": "اكتب بالعربية حصراً. لا تستخدم أي لغة أخرى.",
            "variables": [],
            "max_tokens": 200,
        }

    def get_prompt(self, name: str, variables: dict[str, Any] | None = None) -> str | None:
        prompt = self._prompts.get(name)
        if prompt is None:
            return None
        template = prompt["content"]
        if variables:
            for key, value in variables.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

    def list_prompts(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "version": p["version"], "variables": p["variables"], "max_tokens": p["max_tokens"]}
            for name, p in self._prompts.items()
        ]

    def register_prompt(self, name: str, content: str, version: str = "1.0", variables: list[str] | None = None, max_tokens: int = 500) -> None:
        self._prompts[name] = {
            "version": version,
            "content": content,
            "variables": variables or [],
            "max_tokens": max_tokens,
        }


prompt_manager = PromptManager()


class Evaluator:

    def __init__(self):
        self._results: list[EvaluationResult] = []

    async def evaluate(
        self, prompt: str, response: str, model: str, duration_ms: float,
    ) -> EvaluationResult:
        score = self._compute_score(prompt, response)
        metrics = self._compute_metrics(response)
        result = EvaluationResult(
            id=str(uuid.uuid4()),
            prompt=prompt[:200],
            response=response,
            score=score,
            metrics=metrics,
            model=model,
            duration_ms=duration_ms,
        )
        self._results.append(result)
        self._persist(result)
        return result

    def _compute_score(self, prompt: str, response: str) -> float:
        score = 1.0
        if len(response) < 10:
            score -= 0.3
        forbidden = ["diagnosis:", "treatment:", "medication:", "prescribe", "تشخيص:", "العلاج:", "الدواء:"]
        for phrase in forbidden:
            if phrase in response:
                score -= 0.2
        if len(response) > 5 and " " not in response.strip():
            score -= 0.2
        return round(max(0.0, score), 2)

    def _compute_metrics(self, response: str) -> dict[str, Any]:
        words = response.split()
        return {
            "length_chars": len(response),
            "length_words": len(words),
            "has_arabic": bool(re.search(r"[\u0600-\u06FF]", response)),
            "has_english": bool(re.search(r"[a-zA-Z]", response)),
            "sentences": len(re.split(r"[.!?]+\s*", response.strip())),
        }

    def _persist(self, result: EvaluationResult) -> None:
        try:
            db = next(get_db())
        except Exception:
            return
        try:
            metrics_json = json.dumps(result.metrics, ensure_ascii=False)
            db.execute(
                text("INSERT INTO ai_evaluations (eval_type, prompt, response, score, metrics, model, duration_ms) VALUES (:et, :prompt, :resp, :score, CAST(:metrics AS jsonb), :model, :dur)"),
                {"et": "governance", "prompt": result.prompt, "resp": result.response, "score": result.score, "metrics": metrics_json, "model": result.model, "dur": result.duration_ms},
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("[Governance] evaluation persist failed: %s", exc)
        finally:
            db.close()

    def get_stats(self) -> dict[str, Any]:
        if not self._results:
            return {"count": 0, "avg_score": 0.0, "by_model": {}}
        scores = [r.score for r in self._results if r.score is not None]
        by_model: dict[str, list[float]] = {}
        for r in self._results:
            by_model.setdefault(r.model, []).append(r.score or 0)
        return {
            "count": len(self._results),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "by_model": {model: round(sum(s) / len(s), 2) for model, s in by_model.items()},
            "latest": self._results[-1].__dict__ if self._results else None,
        }


evaluator = Evaluator()
