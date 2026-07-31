#!/usr/bin/env python3
"""
GULA Project Brain — Knowledge Index Generator (PROGRAM-012, Phase 1)
====================================================================
Generates the continuously synchronized Project Brain: a deterministic
knowledge index of the entire repository (structure, modules, services,
endpoints, migrations, ADRs, programs, tests, CI, docs, environments).

The Project Brain is the authoritative knowledge navigation layer. Every
future AI session and every developer MUST consult it before changing code.

Usage:
    python scripts/project_brain.py            # generate docs/brain/PROJECT_BRAIN.md
    python scripts/project_brain.py --json     # also write docs/brain/brain_index.json
    python scripts/project_brain.py --check    # verify brain is fresh (exit 1 if stale)
    python scripts/project_brain.py --stale-days N   # tolerance for --check (default 7)

Outputs:
    docs/brain/PROJECT_BRAIN.md    — human/machine-readable knowledge index (markdown)
    docs/brain/brain_index.json    — machine-readable knowledge index (JSON)

Exit codes:
    0  — success (or brain is fresh in --check mode)
    1  — failure (or brain is stale in --check mode)
"""

from __future__ import annotations

import argparse
import contextlib
import json
import pathlib
import re
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BRAIN_DIR = REPO_ROOT / "docs" / "brain"
BRAIN_MD = BRAIN_DIR / "PROJECT_BRAIN.md"
BRAIN_JSON = BRAIN_DIR / "brain_index.json"

# ── collect ────────────────────────────────────────────────────────────────


def _count_files(path: pathlib.Path, pattern: str) -> int:
    return len(list(path.glob(pattern))) if path.exists() else 0


def _collect_tests() -> dict[str, Any]:
    counts: dict[str, int] = {}
    for name in ("backend/tests", "tests", "shared", "security/tests", "frontend-v3"):
        base = REPO_ROOT / name
        if not base.exists():
            continue
        files = [p for p in base.rglob("test_*.py") if "__pycache__" not in str(p)]
        files += [p for p in base.rglob("*.test.ts") if "node_modules" not in str(p)]
        files += [p for p in base.rglob("*.test.tsx") if "node_modules" not in str(p)]
        counts[name] = len({p.resolve() for p in files})
    return counts


def _collect_routes() -> int:
    """Count FastAPI route registrations via AST (app.include_router / router.get)."""
    routes = 0
    for path in (REPO_ROOT / "backend" / "app").rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        with contextlib.suppress(OSError):
            text = path.read_text(encoding="utf-8", errors="ignore")
        if "APIRouter" not in text and "include_router" not in text:
            continue
        routes += len(
            re.findall(
                r"@(?:router|api)\.(?:get|post|put|patch|delete|websocket)\(",
                text,
            )
        )
    return routes


def _collect_migrations() -> tuple[int, str | None]:
    versions = REPO_ROOT / "backend" / "migrations" / "versions"
    files = sorted(versions.glob("*.py")) if versions.exists() else []
    head = None
    if files:
        try:
            text = files[-1].read_text(encoding="utf-8", errors="ignore")
            head = re.search(r'revision[^"\']*["\']([\w]+)["\']', text)
        except OSError:
            pass
    return len(files), head.group(1) if head else None


def _collect_services() -> dict[str, int]:
    svc_dir = REPO_ROOT / "backend" / "app" / "services"
    return {
        "service_files": _count_files(svc_dir, "*.py"),
        "total_lines": (
            sum(len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) for p in svc_dir.glob("*.py"))
            if svc_dir.exists()
            else 0
        ),
    }


def _collect_modules() -> dict[str, int]:
    areas = {
        "backend/app": "backend/app",
        "shared": "shared",
        "services": "services",
        "ai": "ai",
        "governance": "governance",
        "security": "security",
        "frontend-v3/src": "frontend-v3/src",
        "mobile": "mobile",
    }
    out: dict[str, int] = {}
    for label, rel in areas.items():
        base = REPO_ROOT / rel
        if not base.exists():
            continue
        files = [p for p in base.rglob("*.py") if "__pycache__" not in str(p) and "node_modules" not in str(p)]
        files += [p for p in base.rglob("*.ts") if "node_modules" not in str(p) and ".d.ts" not in str(p)]
        files += [p for p in base.rglob("*.tsx") if "node_modules" not in str(p)]
        lines = sum(len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) for p in files)
        out[label] = {"python_files": len(files), "lines": lines}
    return out


def _collect_docs() -> dict[str, Any]:
    docs = REPO_ROOT / "docs"
    md = [p for p in docs.rglob("*.md") if "node_modules" not in str(p)]
    adrs = sorted(REPO_ROOT.glob("architecture/**/*.md"))
    adrs += sorted((docs / "adr").glob("**/*.md")) if (docs / "adr").exists() else []
    return {
        "docs_markdown_files": len(md),
        "adr_count": len({p.resolve() for p in adrs}),
        "constitution_docs": _count_files(docs / "constitution", "*.md"),
    }


def _collect_programs() -> list[str]:
    """List completed program markers (PROGRAM-*, MISSION-*) referenced in docs."""
    programs: set[str] = set()
    for p in REPO_ROOT.glob("PROGRAM-*.md"):
        programs.add(p.stem)
    for p in REPO_ROOT.glob("MISSION-*.md"):
        programs.add(p.stem)
    for p in (REPO_ROOT / "docs").rglob("*.md"):
        if "node_modules" in str(p):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.findall(r"(PROGRAM-\d+[A-Z]?(?:-[A-Z]+)?|MISSION-\d+[A-Z]?(?:-[A-Z]+)?)", text):
            programs.add(m)
    return sorted(programs)


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", "-1", "--format=%h %s"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _latest_source_mtime() -> float:
    newest = 0.0
    for base in (REPO_ROOT / "backend" / "app", REPO_ROOT / "shared", REPO_ROOT / "governance", REPO_ROOT / "scripts"):
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and "__pycache__" not in str(p) and ".git" not in str(p):
                with contextlib.suppress(OSError):
                    newest = max(newest, p.stat().st_mtime)
    return newest


def collect() -> dict[str, Any]:
    """Gather the full knowledge index. Pure function, no side effects."""
    migrations_n, migrations_head = _collect_migrations()
    backend_app = REPO_ROOT / "backend" / "app"
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "repo": {
            "name": REPO_ROOT.name,
            "root": str(REPO_ROOT),
            "git_head": _git_commit(),
        },
        "counts": {
            "modules": _collect_modules(),
            "routes": _collect_routes(),
            "migrations": migrations_n,
            "migrations_head": migrations_head,
            "services": _collect_services(),
            "models": _count_files(backend_app / "models", "*.py"),
            "tests": _collect_tests(),
            "docs": _collect_docs(),
            "ci_workflows": _count_files(REPO_ROOT / ".github" / "workflows", "*.yml"),
            "dockerfiles": len(list(REPO_ROOT.rglob("Dockerfile")))
            + len(list(REPO_ROOT.rglob("*.dockerfile"))),
        },
        "programs": _collect_programs(),
        "source_freshness": {
            "newest_source_mtime": _latest_source_mtime(),
            "brain_mtime": BRAIN_MD.stat().st_mtime if BRAIN_MD.exists() else 0.0,
        },
    }


# ── render ─────────────────────────────────────────────────────────────────


def _render_table(rows: list[tuple[str, Any]]) -> str:
    return "\n".join(f"| {k} | {v} |" for k, v in rows)


def render_markdown(data: dict[str, Any]) -> str:
    counts = data["counts"]
    mods = counts["modules"]
    tests = counts["tests"]
    docs = counts["docs"]
    mod_lines = sum(m["lines"] for m in mods.values())
    mod_files = sum(m["python_files"] for m in mods.values())
    test_total = sum(tests.values())

    sections: list[str] = []
    sections.append(
        f"""# GULA Platform — Project Brain

> Auto-generated by `scripts/project_brain.py` (PROGRAM-012, Phase 1).
> DO NOT EDIT BY HAND. Regenerate with `make brain` or `python scripts/project_brain.py`.
> Generated: {data['generated_at']}
> Git HEAD: {data['repo']['git_head'] or 'unknown'}
> This is the authoritative knowledge navigation index. Read it before modifying the repository.

---

## 1. Repository Overview

{_render_table([
    ("Repository", data["repo"]["name"]),
    ("Type", "Monorepo (backend, shared, governance, security, frontend-v3, mobile, ai, services)"),
    ("Backend", "FastAPI (Python 3.12) — PostgreSQL + Redis"),
    ("Frontend", "frontend-v3 (React, Arabic-first RTL)"),
    ("Python files (active areas)", mod_files),
    ("Python lines (active areas)", mod_lines),
    ("FastAPI routes (AST scan)", counts["routes"]),
    ("Services (backend/app/services)", counts["services"]["service_files"]),
    ("Models", counts["models"]),
    ("Migrations", f"{counts['migrations']} (head: {counts['migrations_head'] or 'unknown'})"),
    ("Tests (python + frontend files)", test_total),
    ("CI workflows", counts["ci_workflows"]),
    ("Dockerfiles", counts["dockerfiles"]),
    ("Docs (markdown)", docs["docs_markdown_files"]),
    ("ADRs", docs["adr_count"]),
    ("Constitution docs", docs["constitution_docs"]),
])}

---

## 2. Module Inventory

| Area | Python files | Lines |
|---|---|---|
{chr(10).join(f"| `{k}` | {v['python_files']} | {v['lines']} |" for k, v in sorted(mods.items()))}

### 2.1 Test Inventory

| Suite | Test files |
|---|---|
{chr(10).join(f"| `{k}` | {v} |" for k, v in sorted(tests.items()))}

---

## 3. Knowledge Navigation (WHERE IS WHAT)

| Need | Go to |
|---|---|
| AI operating manual (entry point) | `CLAUDE.md` |
| Auto-loaded agent instructions + anchored state | `AGENTS.md` |
| Architecture | `ARCHITECTURE.md`, `docs/architecture/` |
| Constitution (31+ articles) | `docs/constitution/` |
| Machine-enforced constitution engine | `governance/` package, `scripts/constitution_enforcer.py` |
| Certification engine (live API) | `backend/app/certification/` |
| Engineering validators (SOLID/CQRS/DDD) | `backend/app/engineering/validation/` |
| Knowledge graph (AST) | `backend/app/engineering/intelligence/knowledge_graph.py` |
| Zero-drift (frontend↔backend) | `scripts/zero_drift_engine.py`, `docs/certification/` |
| Architecture compliance | `scripts/architecture_compliance_engine.py` |
| Repository scorecard | `scripts/repository_scorecard.py` |
| Tech-debt registry | `scripts/technical_debt_registry.py`, `docs/technical-debt/REGISTRY.md` |
| Security | `security/`, `docs/security/` |
| Permissions & roles | `PERMISSION_CATALOG.md`, `ROLE_CATALOG.md`, `PERMISSION_MATRIX.csv` |
| ADRs | `architecture/`, `docs/adr/` |
| Roadmaps | `ROADMAP.md`, `docs/roadmaps/`, `docs/constitution/30_GULA_ROADMAP_2035.md` |
| Risk register | `security/RISK_REGISTER.md`, `docs/ai/RISK_REGISTER.md` |
| Release history | `CHANGELOG.md`, `docs/reports/`, `reports/` |

---

## 4. Programs & Missions (Knowledge State)

Completed/known programs referenced in the repository:
{chr(10).join(f"- `{p}`" for p in data["programs"])}

---

## 5. Environments & Deployment Targets

- Local: `make up` (docker compose), backend on `:8000` behind nginx gateway `:8080`
- Docker: `docker-compose.yml`, `docker-compose.full.yml`, `docker-compose.scale.yml`
- Kubernetes: `k8s/`, `helm/`
- Terraform: `terraform/`
- Edge: `edge_agent/`, `EDGE_PLATFORM.md`
- National: `nhop-platform/`, `docs/national/`, `docs/sndhs/`
- Android: `mobile/`; CI: `mobile-android.yml`
- Web: frontend-v3 → `vercel.json`; PWA: `frontend-pwa.yml`

---

## 6. Source Freshness

| Metric | Value |
|---|---|
| Newest source mtime | {datetime.fromtimestamp(data['source_freshness']['newest_source_mtime'], tz=UTC).isoformat()} |
| Brain generated at | {data['generated_at']} |

Stale brain if newest source is newer than the brain beyond the configured tolerance
(`--stale-days`, default 7). Regenerate with `make brain`.

---

## 7. Governance Protocol (Program 012/012A)

1. **Read first**: CLAUDE.md → AGENTS.md → PROJECT_BRAIN.md → domain docs.
2. **Plan**: split work into atomic tasks; run impact analysis (files, APIs, tests, docs).
3. **Validate**: `make validate` (enterprise validation engine) before commit.
4. **Certify**: `make certify` gate; consult `backend/app/certification/`.
5. **Document**: update brain (`make brain`), ADR for architectural decisions.
6. **Commit**: conventional commits, atomic, with rollback path.
"""
    )
    return "\n".join(sections)


# ── CLI ────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GULA Project Brain generator")
    parser.add_argument("--json", action="store_true", help="also write brain_index.json")
    parser.add_argument("--check", action="store_true", help="exit 1 if brain is stale")
    parser.add_argument("--stale-days", type=int, default=7, help="stale tolerance in days")
    parser.add_argument("--quiet", action="store_true", help="suppress progress output")
    args = parser.parse_args(argv)

    data = collect()

    if args.check:
        newest = data["source_freshness"]["newest_source_mtime"]
        brain = data["source_freshness"]["brain_mtime"]
        if brain == 0.0:
            print("FATAL: PROJECT_BRAIN.md does not exist — run `make brain`", file=sys.stderr)
            return 1
        stale = newest - brain
        limit = args.stale_days * 86400
        age_days = stale / 86400
        if stale > limit:
            print(f"FAIL: brain is {age_days:.1f} days stale (limit {args.stale_days}) — run `make brain`")
            return 1
        print(f"PASS: brain is {age_days:.1f} days old (limit {args.stale_days} days)")
        return 0

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    BRAIN_MD.write_text(render_markdown(data), encoding="utf-8")
    if not args.quiet:
        print(f"Wrote {BRAIN_MD.relative_to(REPO_ROOT)}")
    if args.json:
        BRAIN_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if not args.quiet:
            print(f"Wrote {BRAIN_JSON.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
