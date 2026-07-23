# GULA Platform

Arabic-first healthcare platform for Iraqi medical laboratories.

## Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.11+) — Gunicorn + Uvicorn |
| Database | PostgreSQL 16 (SQLAlchemy async) |
| Cache | Redis 7 |
| Gateway | nginx (api-gateway) |
| Auth | JWT (HS256) + RBAC (9 roles x 13 permissions) |
| Frontend | React + Firebase (frontend-v2/) or tRPC SPA (client/) |
| Device Bridge | LabLink-Core (ASTM/HL7 instrument integration) |

## Quick Start

```bash
make up              # Start full stack
make health          # Check liveness
make logs-backend    # Tail backend logs
make shell           # Bash into backend container
```

## Development

```bash
# Run tests
cd backend && python -m pytest tests/ -v

# Lint
ruff check backend/app/

# Type check
mypy backend/app/
```

See `CLAUDE.md` for the full developer guide, architecture, migration policy, and quality gates.

## Platform Constitution

This platform is governed by **PROGRAM-CONSTITUTION-001** — permanent amendment
establishing Free First, Open Source First, Self-Hosted First, and Cost Governance
as immutable platform rules. All code, dependencies, infrastructure, and architecture
decisions MUST comply.

| Principle | Summary |
|-----------|---------|
| Free First | Free solution before any paid alternative |
| Open Source First | Open Source before proprietary |
| Self-Hosted First | Self-hosted before SaaS |
| No Vendor Lock-In | Every component replaceable |
| Zero Paid Dependency | Paid requires documented exception |
| Local AI First | Self-hosted inference before API |
| Free Security First | Open-source security tools |

Full policy: `docs/constitution/COST_GOVERNANCE.md`

## Architecture (Monolith-First)

```
Internet → nginx (TLS) → api-gateway → gula-backend (FastAPI) → PostgreSQL 16 + Redis 7
```

The backend monolith in `backend/app/` is the production deployment target.
A parallel microservices tree (`services/`) exists for future decomposition.

## Key Documents

- `CLAUDE.md` — Developer guide, architecture, invariants, commands
- `CHANGELOG.md` — Release history
- `ARCHITECTURE.md` — Architecture overview
- `DOCUMENTATION_INVENTORY.md` — Complete documentation inventory
- `DOCUMENTATION_GAP_ANALYSIS.md` — Documentation gap analysis
- `docs/` — ADRs, SNDHS spec, domain glossary, event catalog, API coverage,
  database schema, workflow catalog, configuration reference, feature matrix,
  UI component catalog, module dependencies, migration guide, compatibility
  matrix, support policy, known limitations

## Project Status

Production-ready. Serving Iraqi medical laboratories.
