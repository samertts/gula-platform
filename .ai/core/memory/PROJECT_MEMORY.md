# .ai/core/memory/PROJECT_MEMORY.md

**Mission:** PROGRAM-KNOWLEDGE-001
**Created:** 2026-08-04
**Last Updated:** 2026-08-04
**Status:** Active

---

## Project Memory — Persistent Engineering Knowledge

This file stores permanent project knowledge that every AI session must inherit.
Never delete entries. Only append or update.

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Language | Python | 3.12 (target) | Backend |
| Framework | FastAPI | Latest | API server |
| Database | PostgreSQL | 16 | Primary data store |
| Cache | Redis | 7.x | Caching, sessions |
| Object Storage | MinIO | Latest | S3-compatible storage |
| Frontend | React + TypeScript | — | Web UI |
| Build | Vite | Latest | Frontend bundler |
| Mobile | Flutter | Latest | Android/iOS |
| AI | Ollama | 0.24.0 | Local inference |
| Container | Docker | 29.1.3 | Containerization |
| Node | Node.js | 24.18.0 | Frontend tooling |
| Package | npm | 11.16.0 | Node packages |
| Rust | Cargo | 1.96.0 | Native tools |
| Python PKG | uv | 0.11.26 | Python packages |
| Linter | Ruff | Latest | Python linting |
| Type Check | mypy | Latest | Python types |
| AI Tool | OpenCode | 1.18.13 | AI assistant |

---

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Monolith-first | Yes | ADR-002: Start monolith, extract services later |
| Primary DB | PostgreSQL | ADR-005: ACID, JSON, FHIR compatibility |
| Cache | Redis | ADR-005: Performance, pub/sub |
| PK Strategy | UUID | ADR-009: Multi-tenant, offline-first |
| FHIR | R4 | ADR-011: National interoperability |
| SBOM | CycloneDX | ADR-012: Supply chain security |
| Identity | Custom (NIAM) | ADR-012: National identity requirements |
| Observability | OTel + Jaeger | ADR-014: Vendor-neutral tracing |
| DR | PITR + WAL | ADR-015: Point-in-time recovery |
| **AI Constitution** | **CONST-000001** | **Supreme AI authority, single source of truth** |

---

## AI Constitution (CONST-000001)

The repository has a **supreme AI constitution** (`AI_OPERATING_CONSTITUTION.md`)
that governs all AI systems. It supersedes rules in AGENTS.md, CLAUDE.md,
COPILOT.md, CODEX.md, GEMINI.md, and .github/copilot-instructions.md.

All AI configuration files now reference the constitution as the single source
of truth. The constitution is never duplicated — only referenced.

---

## Coding Standards

| Rule | Standard |
|---|---|
| Python target | 3.12 |
| Linter | Ruff (target py312) |
| Naming | snake_case (functions, variables), PascalCase (classes) |
| Type hints | Mandatory on public functions |
| Docstrings | Google style |
| Imports | stdlib → third-party → local |
| Max line | 88 characters (Ruff default) |
| Tests | pytest, 100% for new code |
| Frontend | TypeScript strict, ESLint, Prettier |
| Commit | Conventional Commits |
| Branch | Feature branches, no force push |

---

## Naming Standards

| Context | Convention | Example |
|---|---|---|
| Python functions | snake_case | `get_user_by_id()` |
| Python variables | snake_case | `user_name` |
| Python classes | PascalCase | `UserService` |
| Python constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Python modules | snake_case | `user_service.py` |
| TypeScript functions | camelCase | `getUserById()` |
| TypeScript variables | camelCase | `userName` |
| TypeScript classes | PascalCase | `UserService` |
| TypeScript interfaces | PascalCase | `IUserService` |
| TypeScript constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Database tables | snake_case | `users` |
| Database columns | snake_case | `created_at` |
| API endpoints | kebab-case | `/api/v1/user-profile` |
| Git branches | kebab-case | `feature/user-auth` |
| Commit messages | Conventional | `feat: add user auth` |

---

## Preferred Solutions

| Domain | Preferred | Reason |
|---|---|---|
| Database | PostgreSQL | ACID, JSON, FHIR compat |
| Cache | Redis | Performance, pub/sub |
| Object Storage | MinIO | S3-compatible, self-hosted |
| Authentication | JWT + Refresh | Stateless, secure |
| Authorization | RBAC + ABAC | Flexibility |
| API Framework | FastAPI | Performance, typing |
| Frontend Framework | React | Ecosystem, TypeScript |
| Build Tool | Vite | Speed, DX |
| Mobile Framework | Flutter | Cross-platform |
| AI Inference | Ollama | Self-hosted, local |
| Monitoring | Prometheus + Grafana | Open source |
| Tracing | OpenTelemetry + Jaeger | Vendor-neutral |
| Container | Docker | Standard |
| CI/CD | GitHub Actions | Integration |
| Linting (Python) | Ruff | Speed, comprehensive |
| Testing (Python) | pytest | Ecosystem |
| Testing (TS) | Vitest | Speed, Vite integration |

---

## Known Limitations

| Limitation | Impact | Workaround |
|---|---|---|
| System python3 is 3.10 | Must use .venv or uv for 3.12 | Always activate venv |
| Docker Compose v1 broken | Can't use `docker-compose` | Use `docker compose` (v2) |
| mypy times out | Full codebase check fails | Run on specific files |
| WSL2 PATH includes Windows | 22 Windows paths in PATH | Resolved in ENV-001 |

---

## Deployment Topology

| Component | Location | Access |
|---|---|---|
| Backend | Docker container | Internal:5000 |
| Frontend | Nginx | Public:443 |
| PostgreSQL | Docker container | Internal:5432 |
| Redis | Docker container | Internal:6379 |
| MinIO | Docker container | Internal:9000 |
| Ollama | Host system | Local:11434 |

---

## Security Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Encryption | Fernet (shared/security) | Symmetric, fast, simple |
| Auth | JWT + Refresh tokens | Stateless, mobile-friendly |
| RBAC | Role-based + ABAC | National healthcare hierarchy |
| Audit log | Immutable append-only | ISO 15189, CAP compliance |
| Secrets | Environment variables | Never in code |
| CORS | Strict allowlist | No wildcards in production |
| Rate limiting | Per-role limits | API abuse prevention |

---

## Testing Strategy

| Type | Framework | Coverage |
|---|---|---|
| Unit | pytest | All services |
| Integration | pytest + PostgreSQL | API endpoints |
| Frontend unit | Vitest | Utils, hooks |
| Linting | Ruff | Python code |
| Type checking | mypy | Python types |
| Security | bandit | Python SAST |
| CI | GitHub Actions | Every PR |

---

## Future Roadmap

| Item | Priority | Status |
|---|---|---|
| Reduce ruff violations (379 → 0) | HIGH | In progress |
| Frontend component tests | MEDIUM | Planned |
| Identity service tests | MEDIUM | Planned |
| Android/iOS E2E tests | MEDIUM | Planned |
| OpenTelemetry SDK export | LOW | Planned |
| Kubernetes manifests | LOW | Planned |

---

## Lessons Learned

| Date | Lesson | Source |
|---|---|---|
| 2026-08 | PATH deduplication prevents tool resolution conflicts | ENV-001 |
| 2026-08 | NVM should be sole Node manager, not npm prefix | ENV-001 |
| 2026-08 | WSL interop paths add noise to Linux PATH | ENV-001 |
| 2026-07 | Service extraction reduces route files by 71% | PROGRAM-BACKEND-001 |
| 2026-07 | Lazy Redis/Queue prevents startup coupling | PROGRAM-BACKEND-001 |
| 2026-07 | Test DDL optimization cuts auth setup by 53% | PROGRAM-BACKEND-001 |
| 2026-07 | Westgard 2-2s rule must be checked before 1-2s | PROGRAM-BACKEND-001 |

---

## Rejected Solutions

| Solution | Reason | Date |
|---|---|---|
| SaaS AI APIs | Violates Local AI First constitution | 2026-05 |
| Vendor-specific DB features | Violates No Vendor Lock-In | 2026-05 |
| Commercial security tools | Violates Free Security First | 2026-05 |
| Proprietary CI/CD | Violates Open Source First | 2026-05 |

---

## Changelog

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial project memory |
