from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.compiler.models import Technology, TechnologyStatus


class TechnologyCatalog:
    _instance: TechnologyCatalog | None = None
    CATALOG_PATH = Path(__file__).resolve().parent / "technology_catalog.json"

    def __new__(cls) -> TechnologyCatalog:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._technologies: list[Technology] = []
            cls._instance._loaded = False
        return cls._instance

    def load(self) -> None:
        if self._loaded:
            return
        if self.CATALOG_PATH.exists():
            data = json.loads(self.CATALOG_PATH.read_text(encoding="utf-8"))
            self._technologies = [Technology(**t) for t in data.get("technologies", [])]
        else:
            self._technologies = self._default_catalog()
            self.save()
        self._loaded = True

    def save(self) -> None:
        data = {
            "version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "technologies": [t.to_dict() for t in self._technologies],
        }
        self.CATALOG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @property
    def technologies(self) -> list[Technology]:
        self.load()
        return self._technologies

    def search(self, query: str = "", category: str = "", status: str = "") -> list[Technology]:
        results = self.technologies
        if query:
            q = query.lower()
            results = [t for t in results if q in t.name.lower() or q in t.category.lower()]
        if category:
            results = [t for t in results if t.category.lower() == category.lower()]
        if status:
            results = [t for t in results if t.status.value == status.lower()]
        return results

    def get_by_name(self, name: str) -> Technology | None:
        for t in self.technologies:
            if t.name.lower() == name.lower():
                return t
        return None

    def get_by_category(self, category: str) -> list[Technology]:
        return [t for t in self.technologies if t.category.lower() == category.lower()]

    def get_approved(self) -> list[Technology]:
        return [t for t in self.technologies if t.status == TechnologyStatus.APPROVED]

    def get_certified(self) -> list[Technology]:
        return [t for t in self.technologies if t.status == TechnologyStatus.CERTIFIED]

    def get_forbidden(self) -> list[Technology]:
        return [t for t in self.technologies if t.status == TechnologyStatus.FORBIDDEN]

    def get_categories(self) -> list[str]:
        return sorted(set(t.category for t in self.technologies))

    def get_sovereignty_score(self, name: str) -> int:
        tech = self.get_by_name(name)
        return tech.sovereignty_score if tech else 0

    def get_cost(self, name: str) -> float:
        tech = self.get_by_name(name)
        return tech.cost if tech else 0.0

    def get_open_source_alternatives(self, name: str) -> list[Technology]:
        tech = self.get_by_name(name)
        if not tech or not tech.open_source_alternative:
            return []
        return self.search(query=tech.open_source_alternative.split(",")[0].strip())

    def add_technology(self, tech: Technology) -> None:
        self.load()
        existing = self.get_by_name(tech.name)
        if existing:
            self._technologies.remove(existing)
        self._technologies.append(tech)
        self.save()

    def remove_technology(self, name: str) -> bool:
        self.load()
        tech = self.get_by_name(name)
        if tech:
            self._technologies.remove(tech)
            self.save()
            return True
        return False

    def set_status(self, name: str, status: TechnologyStatus) -> bool:
        tech = self.get_by_name(name)
        if tech:
            tech.status = status
            self.save()
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "technologies": [t.to_dict() for t in self.technologies],
            "count": len(self.technologies),
            "categories": self.get_categories(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def _default_catalog(self) -> list[Technology]:
        return [
            Technology("PostgreSQL", "database", "PostgreSQL", "PostgreSQL Global Development Group", "mature", "large", 95, 0, 95, 0, 0, "Community", "", "Oracle DB, MSSQL", "low", 90, 95, 100, TechnologyStatus.CERTIFIED),
            Technology("Redis", "cache", "BSD", "Redis Ltd", "mature", "large", 90, 1, 90, 0, 0, "Community", "", "AWS ElastiCache", "low", 85, 90, 100, TechnologyStatus.CERTIFIED),
            Technology("MinIO", "storage", "AGPLv3", "MinIO Inc", "mature", "medium", 85, 2, 80, 0, 0, "Community/Apache", "", "AWS S3", "medium", 80, 85, 95, TechnologyStatus.CERTIFIED),
            Technology("Grafana", "monitoring", "AGPLv3", "Grafana Labs", "mature", "large", 85, 3, 95, 0, 0, "Community", "", "Datadog", "medium", 85, 90, 90, TechnologyStatus.CERTIFIED),
            Technology("Prometheus", "metrics", "Apache 2.0", "CNCF", "mature", "large", 90, 0, 85, 0, 0, "Community", "", "Datadog, New Relic", "medium", 90, 90, 100, TechnologyStatus.CERTIFIED),
            Technology("Loki", "logging", "AGPLv3", "Grafana Labs", "mature", "large", 85, 1, 80, 0, 0, "Community", "", "Datadog Logs, Logz.io", "medium", 85, 85, 90, TechnologyStatus.CERTIFIED),
            Technology("Ollama", "ai", "MIT", "Community", "active", "medium", 80, 0, 85, 0, 0, "Community", "", "OpenAI, Anthropic", "low", 75, 85, 95, TechnologyStatus.CERTIFIED),
            Technology("Keycloak", "auth", "Apache 2.0", "CNCF", "mature", "large", 90, 2, 90, 0, 0, "Community", "", "Auth0, Okta", "medium", 80, 90, 100, TechnologyStatus.CERTIFIED),
            Technology("Authentik", "auth", "MIT", "Community", "active", "medium", 80, 0, 80, 0, 0, "Community", "", "Auth0, Okta", "medium", 75, 85, 95, TechnologyStatus.APPROVED),
            Technology("Nginx", "proxy", "BSD", "NGINX Inc", "mature", "large", 90, 1, 95, 0, 0, "Community", "", "F5, HAProxy (paid)", "low", 95, 95, 95, TechnologyStatus.CERTIFIED),
            Technology("Traefik", "proxy", "MIT", "Traefik Labs", "mature", "medium", 85, 0, 85, 0, 0, "Community", "", "F5, NGINX Plus", "low", 85, 90, 95, TechnologyStatus.APPROVED),
            Technology("RabbitMQ", "messaging", "MPL 2.0", "VMware", "mature", "large", 85, 3, 85, 0, 0, "Community", "", "AWS SQS, Google Pub/Sub", "medium", 80, 85, 95, TechnologyStatus.CERTIFIED),
            Technology("NATS", "messaging", "Apache 2.0", "CNCF", "mature", "medium", 90, 0, 80, 0, 0, "Community", "", "AWS SQS, Google Pub/Sub", "medium", 95, 85, 100, TechnologyStatus.APPROVED),
            Technology("OpenSearch", "search", "Apache 2.0", "AWS/Community", "mature", "large", 85, 2, 85, 0, 0, "Community", "", "Elastic Cloud", "medium", 85, 85, 90, TechnologyStatus.CERTIFIED),
            Technology("Qdrant", "vector_db", "Apache 2.0", "Community", "active", "medium", 80, 0, 80, 0, 0, "Community", "", "Pinecone, Weaviate Cloud", "medium", 85, 85, 95, TechnologyStatus.APPROVED),
            Technology("ChromaDB", "vector_db", "Apache 2.0", "Community", "active", "small", 75, 0, 70, 0, 0, "Community", "", "Pinecone", "low", 70, 80, 95, TechnologyStatus.EXPERIMENTAL),
            Technology("Vault Community", "secrets", "MPL 2.0", "HashiCorp", "mature", "large", 90, 1, 90, 0, 0, "Community", "", "AWS Secrets Manager, Azure Key Vault", "medium", 80, 90, 95, TechnologyStatus.CERTIFIED),
            Technology("WireGuard", "vpn", "GPLv2", "Community", "mature", "medium", 95, 0, 80, 0, 0, "Community", "", "OpenVPN (Access Server)", "low", 95, 90, 100, TechnologyStatus.CERTIFIED),
            Technology("Let's Encrypt", "tls", "Mozilla Public License", "Internet Security Research Group", "mature", "large", 95, 0, 95, 0, 0, "Community", "", "Commercial CA certificates", "low", 90, 95, 100, TechnologyStatus.CERTIFIED),
            Technology("Fail2Ban", "security", "GPLv2", "Community", "mature", "medium", 85, 0, 75, 0, 0, "Community", "", "CrowdStrike, Cloudflare WAF (paid)", "low", 80, 85, 100, TechnologyStatus.CERTIFIED),
            Technology("CrowdSec", "security", "MIT", "Community", "active", "medium", 80, 0, 80, 0, 0, "Community", "", "Cloudflare WAF (paid)", "low", 80, 85, 95, TechnologyStatus.APPROVED),
            Technology("OpenTelemetry", "observability", "Apache 2.0", "CNCF", "mature", "large", 90, 0, 90, 0, 0, "Community", "", "Datadog, New Relic agents", "low", 85, 95, 100, TechnologyStatus.CERTIFIED),
            Technology("Docker", "container", "Apache 2.0", "Docker Inc", "mature", "large", 85, 5, 95, 0, 0, "Community", "", "ContainerD (standalone)", "medium", 85, 95, 90, TechnologyStatus.CERTIFIED),
            Technology("Kubernetes", "orchestration", "Apache 2.0", "CNCF", "mature", "large", 85, 4, 95, 0, 0, "Community", "", "AWS EKS, Azure AKS, Google GKE", "high", 80, 90, 85, TechnologyStatus.APPROVED),
            Technology("FastAPI", "framework", "MIT", "Community", "mature", "large", 90, 0, 95, 0, 0, "Community", "", "Django REST, Flask", "low", 95, 95, 100, TechnologyStatus.CERTIFIED),
            Technology("SQLAlchemy", "orm", "MIT", "Community", "mature", "large", 90, 0, 95, 0, 0, "Community", "", "Django ORM, Prisma", "low", 85, 95, 100, TechnologyStatus.CERTIFIED),
            Technology("React", "frontend", "MIT", "Meta/Community", "mature", "large", 85, 2, 95, 0, 0, "Community", "", "Angular, Vue (also OSS)", "medium", 90, 90, 90, TechnologyStatus.CERTIFIED),
            Technology("OpenAI API", "ai", "Proprietary", "OpenAI", "mature", "large", 70, 0, 95, 0.02, 0.02, "OpenAI", "Ollama, HuggingFace", "medium", 95, 80, 20, 5, TechnologyStatus.FORBIDDEN),
            Technology("Anthropic API", "ai", "Proprietary", "Anthropic", "mature", "large", 70, 0, 90, 0.03, 0.03, "Anthropic", "Ollama, HuggingFace", "medium", 95, 80, 20, 5, TechnologyStatus.FORBIDDEN),
            Technology("Auth0", "auth", "Proprietary", "Okta", "mature", "large", 85, 0, 95, 0.00, 0.00, "Okta", "Keycloak, Authentik", "medium", 85, 85, 10, 5, TechnologyStatus.FORBIDDEN),
            Technology("Firebase", "baas", "Proprietary", "Google", "mature", "large", 80, 1, 90, 0.00, 0.00, "Google", "Supabase (limited)", "high", 80, 75, 5, 5, TechnologyStatus.FORBIDDEN),
            Technology("Supabase", "baas", "Apache 2.0", "Supabase Inc", "active", "medium", 75, 0, 80, 0.00, 0.00, "Supabase", "Self-hosted PostgreSQL + API", "medium", 80, 80, 40, 50, TechnologyStatus.EXPERIMENTAL),
            Technology("Elastic Cloud", "search", "Proprietary", "Elastic", "mature", "large", 85, 3, 90, 0.00, 0.00, "Elastic", "OpenSearch", "medium", 90, 85, 15, 5, TechnologyStatus.FORBIDDEN),
            Technology("Datadog", "monitoring", "Proprietary", "Datadog Inc", "mature", "large", 85, 0, 95, 0.00, 0.00, "Datadog", "Grafana + Prometheus + Loki", "high", 90, 80, 5, 5, TechnologyStatus.FORBIDDEN),
        ]
