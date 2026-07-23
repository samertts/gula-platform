from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from governance.catalogs.technology_catalog import TechnologyCatalog
from governance.catalogs.dependency_registry import DependencyRegistry
from governance.compiler.models import Recommendation
from governance.constitution_engine import ConstitutionEngine


class AIRecommendationEngine:
    def __init__(self) -> None:
        self.catalog = TechnologyCatalog()
        self.registry = DependencyRegistry()
        self.engine = ConstitutionEngine()

    def recommend(self, query: str, category: str = "", max_results: int = 5) -> Recommendation:
        context = {
            "query": query,
            "category": category,
            "existing_platform": self._search_existing_platform(query),
            "technology_catalog": self._search_catalog(query, category),
            "dependency_registry": self._search_registry(query),
            "architecture_rules": self._get_applicable_rules(query),
        }

        evaluated = self._evaluate_options(context)
        ranked = self._rank_options(evaluated)
        explanation = self._generate_explanation(ranked, context)

        return Recommendation(
            query=query,
            results=evaluated,
            ranked=ranked[:max_results],
            explanation=explanation,
            total_evaluated=len(evaluated),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _search_existing_platform(self, query: str) -> list[dict[str, Any]]:
        return []

    def _search_catalog(self, query: str, category: str = "") -> list[dict[str, Any]]:
        results = self.catalog.search(query=query, category=category)
        return [t.to_dict() for t in results]

    def _search_registry(self, query: str) -> list[dict[str, Any]]:
        results = self.registry.search(query=query)
        return [d.to_dict() for d in results]

    def _get_applicable_rules(self, query: str) -> list[dict[str, Any]]:
        return [{"id": r.id, "title": r.title, "severity": r.severity.value} for r in self.engine.rules[:10]]

    def _evaluate_options(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        options: list[dict[str, Any]] = []

        for tech in context.get("technology_catalog", []):
            is_oss = tech.get("license", "").lower() not in ("proprietary", "commercial")
            constitution_result = self.engine.evaluate_technology(tech["name"], {
                "license": tech.get("license", ""),
                "cost": tech.get("cost", 0),
                "vendor": tech.get("vendor", ""),
                "is_open_source": is_oss,
                "is_self_hosted": tech.get("cost", 0) == 0,
            })

            options.append({
                "name": tech["name"],
                "category": tech.get("category", ""),
                "license": tech.get("license", ""),
                "cost": tech.get("cost", 0),
                "sovereignty_score": tech.get("sovereignty_score", 0),
                "security_score": tech.get("security_score", 0),
                "constitution_score": constitution_result.score,
                "is_open_source": is_oss,
                "status": tech.get("status", ""),
                "vendor": tech.get("vendor", ""),
                "documentation_score": tech.get("documentation_score", 0),
                "open_source_alternative": tech.get("open_source_alternative", ""),
                "commercial_alternative": tech.get("commercial_alternative", ""),
            })

        return options

    def _rank_options(self, options: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for opt in options:
            score = 0.0
            score += (opt.get("constitution_score", 0) / 100) * 30
            score += (opt.get("sovereignty_score", 0) / 100) * 20
            score += (opt.get("security_score", 0) / 100) * 15
            score += (opt.get("documentation_score", 0) / 100) * 10
            if opt.get("is_open_source", False):
                score += 15
            if opt.get("cost", 0) == 0:
                score += 10
            opt["rank_score"] = round(score, 2)

        return sorted(options, key=lambda x: x["rank_score"], reverse=True)

    def _generate_explanation(self, ranked: list[dict[str, Any]], context: dict[str, Any]) -> str:
        if not ranked:
            return "No suitable options found in the Technology Catalog."

        top = ranked[0]
        parts = [f"Top recommendation: {top['name']} (score: {top['rank_score']})"]
        if top.get("is_open_source"):
            parts.append(f"Open source ({top['license']}) — aligned with Open Source First policy")
        if top.get("cost", 0) == 0:
            parts.append("Free of cost — aligned with Free First policy")
        if top.get("sovereignty_score", 0) >= 90:
            parts.append("High sovereignty score — aligned with Platform Sovereignty policy")

        if len(ranked) > 1:
            parts.append(f"Alternative: {ranked[1]['name']} (score: {ranked[1]['rank_score']})")

        return " | ".join(parts)

    def never_recommend_commercial_first(self, query: str) -> bool:
        rec = self.recommend(query)
        for r in rec.ranked:
            if r.get("cost", 0) == 0 or r.get("is_open_source", False):
                return True
        return False
