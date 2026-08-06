# GULA Platform — Master Risk Register (PROGRAM-BETA)

**Date:** 2026-08-06
**Scope:** Consolidated risk register: Architect engine (10 strategic), the Phase 1–8
program findings, and residual WARNs from prior programs.

**Legend:** 🔴 Critical / 🟠 High / 🟡 Medium / 🔵 Low

---

## 1. Strategic Risks (Architect engine — 10 registered)

| Risk | Class | Guidance |
|---|---|---|
| Identity platform coupling to national federation roadmap | Strategic | Keep NIAM pluggable; federation via adapter, never hard-couple |
| Offline-first sync conflicts across governorate partitions | Data | CRDT/outbox; idempotent reconciliation; deterministic conflict policy |
| Governorate data residency and national aggregation conflict | Compliance | National layer only; country-agnostic engine (architecture HARD gate) |
| Analyzer protocol fragmentation across laboratory hardware | Integration | Canonical provider interface + per-protocol adapters |
| Database and storage growth at national scale | Capacity | Partitioning + tiered storage + retention roadmap |
| (6 more in `.ai/core/architect/state/risks/register.json`) | Strategic | Reviewed by `architect-risk` |

## 2. Program Findings (Phase 1–8)

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | SQL injection — `ai/knowledge_graph.py::create_node` (interpolated JSON) | 🔴 High (CWE-89) | **FIXED** — bind params + CAST jsonb; regression test |
| 2 | react-router ≤8.2.0 RSC-CSRF advisory (HIGH) | 🟠 High | **FIXED** — migrated to 8.3.0 patched; 0 audit vulns |
| 3 | `reencrypt_encryption_key.py` identifier injection | 🟡 Medium | **FIXED** — `_validate_identifier` regex guard |
| 4 | nginx frontend missing security headers | 🟡 Medium | **FIXED** — CSP/HSTS/frame-ancestors/nosniff added |
| 5 | `pg_dump` version mismatch vs server (v14 host ↔ v16 server) | 🟡 Medium | **MITIGATED** — backup must run server-matching client; runbook note |
| 6 | Eager route import ~20-24 s at worker boot | 🔵 Low | Tracked; once-per-worker, not per-request |
| 7 | Self-heal incident log `/var/log` permission-dependent | 🔵 Low | Graceful degradation verified |
| 8 | Trivy container scan not run this session | 🔵 Low | Tool absent locally; wired in CI security gate |

## 3. Prior-Program WARNs (burn-down status)

| WARN | Status |
|---|---|
| Cloud snapshot restore | 🟡 Open — `continuous-backup.sh` S3 WAL covers RPO; snapshot-restore drill pending |
| Frontend `/metrics` page | 🔵 Open — backend endpoints done; UI page pending |
| ENCRYPTION_KEY rotation re-encryption | 🔵 Open — reencrypt script hardened + tested; rotation runbook pending |
| Shared Core 57 reimplementation findings | 🔵 Acknowledged debt (baseline gate) — migrate to canonical providers one at a time |

## 4. Top-3 Next Risk Actions
1. **Stand up a real restore-from-S3 drill** (quarterly DR cadence) to close the cloud-snapshot WARN.
2. **Pin the backup toolchain** to the server's pg major version in CI/runbook.
3. **Begin migrating the 57 acknowledged Shared Core reimplementations** to canonical
   providers (identity/notification/audit/barcode/QR/encryption) under the architecture gate.

## 5. Verdict

No critical or high unmitigated risks remain in the verified scope. All Phase 1–8
findings are fixed, mitigated, or explicitly tracked with owners.
