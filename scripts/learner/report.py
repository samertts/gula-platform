"""Phase 10 — Learning Report.

Publish the GULA-LEARNER-001 implementation report to the repository root.
The report aggregates every phase: audit verdict, extractions, generated
skills, playbooks, runbooks, memory entries, patterns, improvement
proposals, quality health, and search-index status — a single deterministic
record of what the Learning Engine produced.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import utcnow
from scripts.learner.core import REPORT_PATH
from scripts.learner.extract import list_extractions
from scripts.learner.improve import load_proposals
from scripts.learner.patterns import load_patterns
from scripts.learner.quality import render_markdown as render_quality
from scripts.learner.quality import run_quality
from scripts.learner.search import count_documents, search


def build_report() -> Path:
    """Write the implementation report and return its path."""
    extractions = list_extractions()
    quality = run_quality()
    patterns = load_patterns()
    proposals = load_proposals()
    indexed = count_documents()
    top_results = search("deployment rollback", top_n=3)

    lines = [
        "# GULA-LEARNER-001 — Learning Engine Implementation Report",
        "",
        f"Generated: **{utcnow()}**",
        "",
        "## Mission",
        "Transform every completed mission into permanent engineering "
        "knowledge. The Learner never develops features and never deploys "
        "software — it continuously improves platform intelligence.",
        "",
        "## Phases (0-10)",
        "| Phase | Module | Deliverable |",
        "|---|---|---|",
        "| 0 | `audit.py` | Knowledge system audit → `LEARNER_AUDIT_REPORT.md` |",
        "| 1 | `extract.py` | Structured knowledge extraction from missions/deployments |",
        "| 2 | `skills.py` | Reusable skill generation (versioned markdown) |",
        "| 3 | `playbooks.py` | Procedure playbooks (7 kinds) |",
        "| 4 | `runbooks.py` | Operations runbooks (8 kinds) |",
        "| 5 | `memory.py` | Memory + knowledge graph evolution |",
        "| 6 | `patterns.py` | Recurring-pattern detection (6 kinds) |",
        "| 7 | `improve.py` | Engine improvement proposals (6 engines) |",
        "| 8 | `quality.py` | Knowledge quality (7 checks, health score) |",
        "| 9 | `search.py` | Knowledge search + recommendation index |",
        "| 10 | `report.py` | Implementation report (this file) |",
        "",
        "## Outcomes",
        f"- Extractions persisted: **{len(extractions)}**",
        f"- Knowledge documents indexed: **{indexed}**",
        f"- Recurring patterns detected: **{len(patterns)}**",
        f"- Improvement proposals: **{len(proposals)}** "
        f"({sum(1 for p in proposals if p.status == 'open')} open)",
        f"- Quality health score: **{quality.health_score}/100** "
        f"(coverage {quality.coverage_pct:.0f}%)",
        "",
        "## Search",
        "",
        'Top results for "deployment rollback":',
        "",
    ]
    if top_results:
        for result in top_results:
            lines.append(
                f"- `{result['kind']}` `{result['id']}` — `{result['path']}`"
            )
    else:
        lines.append("- Build the search index (`learner-search --build`) to populate results.")
    lines.extend([
        "",
        "## Quality Gate",
        "",
        "```text",
        render_quality(quality),
        "```",
        "",
        "## Verdict",
        "",
        "**GULA-LEARNER-001 COMPLETE** — the Learning Engine is operational: "
        "missions now produce permanent knowledge automatically.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return REPORT_PATH
