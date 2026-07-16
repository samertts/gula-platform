from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app._compat import UTC

logger = logging.getLogger("gula.knowledge_graph.adr")

_ADR_FRONTMATTER_RE = re.compile(r"^#\s+(ADR-\d+):\s+(.+)$", re.MULTILINE)
_ADR_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*(\w+)")
_ADR_DATE_RE = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})")
_ADR_DECIDERS_RE = re.compile(r"\*\*Deciders:\*\*\s*(.+)$", re.MULTILINE)
_ADR_CONTEXT_RE = re.compile(r"^##\s+Context\n+(.+?)(?=^##)", re.MULTILINE | re.DOTALL)
_ADR_DECISION_RE = re.compile(r"^##\s+Decision\n+(.+?)(?=^##)", re.MULTILINE | re.DOTALL)
_ADR_CONS_RE = re.compile(r"^##\s+Consequences\n+(.+?)(?=^##)", re.MULTILINE | re.DOTALL)
_ADR_ALT_RE = re.compile(r"^##\s+Alternatives Considered\n+(.+?)(?=^##)", re.MULTILINE | re.DOTALL)
_DOMAIN_TAGS = {
    "architecture": ["architecture", "monolith", "microservice", "decomposition"],
    "security": ["security", "auth", "encryption", "jwt", "rbac", "authentication", "authorization"],
    "integration": ["integration", "api", "fhir", "hl7", "astm", "sndhs", "national", "device"],
    "infrastructure": ["infrastructure", "deployment", "docker", "kubernetes", "database", "storage"],
    "data": ["data", "model", "schema", "migration", "pii", "phi", "patient", "audit"],
    "quality": ["quality", "testing", "ci", "lint", "observability", "monitoring"],
}


def _infer_domain(title: str, context: str) -> str:
    combined = f"{title} {context}".lower()
    scores: dict[str, int] = {}
    for domain, keywords in _DOMAIN_TAGS.items():
        for kw in keywords:
            if kw in combined:
                scores[domain] = scores.get(domain, 0) + 1
    if scores:
        return max(scores, key=scores.get)
    return "general"


@dataclass
class ADRRecord:
    adr_id: str
    title: str
    status: str = "PROPOSED"
    context: str = ""
    decision: str = ""
    consequences: str = ""
    options_considered: list[str] = field(default_factory=list)
    domain: str = ""
    date: str = ""
    deciders: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    superseded_by: str | None = None
    related_adrs: list[dict] = field(default_factory=list)
    source_path: str = ""

    def to_dict(self) -> dict:
        return {
            "adr_id": self.adr_id,
            "title": self.title,
            "status": self.status,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "options_considered": self.options_considered,
            "domain": self.domain,
            "date": self.date,
            "deciders": self.deciders,
            "references": self.references,
            "superseded_by": self.superseded_by,
            "related_adrs": self.related_adrs,
            "source_path": self.source_path,
        }


class ADRManager:
    def __init__(self):
        self._adrs: dict[str, ADRRecord] = {}
        self._next_id: int = 1

    def create_adr(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str = "",
        options: list[str] | None = None,
        domain: str | None = None,
        deciders: list[str] | None = None,
        references: list[str] | None = None,
    ) -> ADRRecord:
        adr_id = f"ADR-{self._next_id:03d}"
        self._next_id += 1
        inferred = domain or _infer_domain(title, context)
        record = ADRRecord(
            adr_id=adr_id,
            title=title,
            status="PROPOSED",
            context=context,
            decision=decision,
            consequences=consequences,
            options_considered=options or [],
            domain=inferred,
            date=datetime.now(UTC).strftime("%Y-%m-%d"),
            deciders=deciders or [],
            references=references or [],
        )
        self._adrs[adr_id] = record
        logger.info(
            "ADR created: %s — %s (domain=%s, status=PROPOSED)",
            adr_id,
            title,
            inferred,
        )
        self._create_auto_adr_nodes(record)
        return record

    def get_adr(self, adr_id: str) -> ADRRecord | None:
        return self._adrs.get(adr_id)

    def list_adrs(self, status: str | None = None, domain: str | None = None) -> list[ADRRecord]:
        results = list(self._adrs.values())
        if status:
            results = [r for r in results if r.status.upper() == status.upper()]
        if domain:
            results = [r for r in results if r.domain == domain]
        return sorted(results, key=lambda r: r.adr_id)

    def update_status(self, adr_id: str, new_status: str) -> ADRRecord | None:
        record = self._adrs.get(adr_id)
        if not record:
            return None
        valid = {"PROPOSED", "ACCEPTED", "DEPRECATED", "SUPERSEDED"}
        upper = new_status.upper()
        if upper not in valid:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of {valid}")
        record.status = upper
        logger.info("ADR %s status updated to %s", adr_id, upper)
        return record

    def link_adr(self, adr_id: str, related_adr_id: str, relationship: str = "RELATES_TO") -> ADRRecord | None:
        record = self._adrs.get(adr_id)
        related = self._adrs.get(related_adr_id)
        if not record or not related:
            return None
        link = {"adr_id": related_adr_id, "title": related.title, "relationship": relationship}
        if link not in record.related_adrs:
            record.related_adrs.append(link)
        if relationship == "SUPERSEDES":
            related.superseded_by = adr_id
            related.status = "SUPERSEDED"
        elif relationship == "SUPERSEDED_BY":
            record.superseded_by = related_adr_id
            record.status = "SUPERSEDED"
        logger.info("ADR %s linked to %s as %s", adr_id, related_adr_id, relationship)
        return record

    def generate_adr_index(self) -> dict:
        by_status: dict[str, list[str]] = {}
        by_domain: dict[str, list[str]] = {}
        for record in self._adrs.values():
            by_status.setdefault(record.status, []).append(record.adr_id)
            by_domain.setdefault(record.domain, []).append(record.adr_id)
        return {
            "total": len(self._adrs),
            "by_status": {k: {"count": len(v), "adrs": v} for k, v in by_status.items()},
            "by_domain": {k: {"count": len(v), "adrs": v} for k, v in by_domain.items()},
            "adrs": [r.to_dict() for r in sorted(self._adrs.values(), key=lambda x: x.adr_id)],
        }

    def load_from_docs(self, adr_dir: str | None = None) -> int:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        )
        docs_adr = adr_dir or os.path.join(project_root, "docs", "adr")
        if not os.path.isdir(docs_adr):
            logger.warning("ADR directory not found: %s", docs_adr)
            return 0
        count = 0
        for fname in sorted(os.listdir(docs_adr)):
            if not fname.endswith(".md") or fname == "README.md":
                continue
            fpath = os.path.join(docs_adr, fname)
            try:
                content = Path(fpath).read_text(encoding="utf-8")
                record = self._parse_adr_markdown(content, fname)
                if record:
                    self._adrs[record.adr_id] = record
                    count += 1
            except Exception as exc:
                logger.warning("Failed to parse ADR %s: %s", fname, exc)
        # Set next_id based on existing ADRs
        max_num = 0
        for adr_id in self._adrs:
            m = re.match(r"ADR-(\d+)", adr_id)
            if m:
                max_num = max(max_num, int(m.group(1)))
        self._next_id = max_num + 1
        logger.info("Loaded %d ADRs from %s", count, docs_adr)
        return count

    def search(self, query: str) -> list[ADRRecord]:
        q = query.lower()
        results = []
        for record in self._adrs.values():
            if (
                q in record.adr_id.lower()
                or q in record.title.lower()
                or q in record.context.lower()
                or q in record.decision.lower()
                or q in record.domain.lower()
            ):
                results.append(record)
        return results

    def _create_auto_adr_nodes(self, record: ADRRecord) -> None:
        try:
            from app.database import SessionLocal

            from .engine import _get_or_create_node
            from .models import NodeType

            db = SessionLocal()
            try:
                _get_or_create_node(
                    db,
                    NodeType.ADR,
                    record.title,
                    f"gula.adr.{record.adr_id}",
                    description=record.context[:500],
                    metadata=record.to_dict(),
                    tags=["adr", record.domain, record.status.lower()],
                )
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
        except Exception:
            pass

    def _parse_adr_markdown(self, content: str, filename: str) -> ADRRecord | None:
        content.split("\n")
        title_match = _ADR_FRONTMATTER_RE.search(content)
        if not title_match:
            return None
        adr_id = title_match.group(1)
        title = title_match.group(2).strip()

        status_match = _ADR_STATUS_RE.search(content)
        status = status_match.group(1).upper() if status_match else "PROPOSED"

        date_match = _ADR_DATE_RE.search(content)
        date = date_match.group(1) if date_match else ""

        deciders_match = _ADR_DECIDERS_RE.search(content)
        deciders = [d.strip() for d in deciders_match.group(1).split(",")] if deciders_match else []

        ctx_match = _ADR_CONTEXT_RE.search(content)
        context = ctx_match.group(1).strip() if ctx_match else ""

        dec_match = _ADR_DECISION_RE.search(content)
        decision = dec_match.group(1).strip() if dec_match else ""

        cons_match = _ADR_CONS_RE.search(content)
        consequences = cons_match.group(1).strip() if cons_match else ""

        alt_match = _ADR_ALT_RE.search(content)
        options = []
        if alt_match:
            alt_text = alt_match.group(1)
            options = [line.strip().lstrip("- ") for line in alt_text.split("\n") if line.strip().startswith("- ")]

        domain = _infer_domain(title, context)

        return ADRRecord(
            adr_id=adr_id,
            title=title,
            status=status,
            context=context,
            decision=decision,
            consequences=consequences,
            options_considered=options,
            domain=domain,
            date=date,
            deciders=deciders,
            source_path=filename,
        )


adr_manager = ADRManager()
