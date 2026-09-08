# GULA Intelligent Platform Core

**Deterministic, AI-free platform self-knowledge.** Generated at HEAD `eb76689`.
Implementation: `tools/gula_intel/` · Tests: `tools/gula_intel/tests/`

## 1. Principle

Intelligence here means *system knowledge + rules + contracts + evidence*, not a model.
No module imports or calls an AI provider; a test enforces that. An AI layer may later
consume these outputs to explain or prioritise, but never to decide.

## 2. Phase 1 — Discovery: what already existed

The repository already had substantial capability. It was reused, not duplicated.

| Capability | Existing artefact | Verdict |
|---|---|---|
| Endpoint/module inventory | `docs/api/backend_inventory.json` (763 endpoints, 50 modules) | **Reused** |
| Findings registry | `docs/technical-debt/registry.json` (647 items) | **Reused as a source** |
| Audited findings | `docs/architecture/GULA_MASTER_NEGATIVE_REGISTER.json` | **Reused as a source** |
| Frontend↔backend drift | `scripts/zero_drift_engine.py`, `docs/contract-audit/generated/` | Exists — not re-implemented |
| Change-aware quality gate | `scripts/quality_changed_files_gate.py` | Exists — complements test selection |
| Migration integrity | `backend/tests/migrations/test_migration_graph_integrity.py` | **Reused as verification** |
| Certification/audit scripts | `enterprise_governance_certification.py`, `audit_verifier.py`, `quality_gate.py` | Exist |

**The gap** was never inventory or gates individually — it was the connective tissue:
no single deterministic layer unified inventory + rules + findings + evidence + impact,
with stable identities and recurrence memory. That gap is what this core fills.

Not covered by any prior artefact and added here: **ORM table ownership**, the
**Alembic graph parsed statically**, and **state-machine transition tables**.

## 3. What the core provides

- **Self-knowledge** (`inventory.py`) — 828 mapped tables, 101 migrations, 763 endpoints,
  50 modules. Pure AST parsing: no application import, no database connection.
- **Detectors** (`detectors.py`) — five rules with stable ids, severity, rationale,
  remediation and verification method.
- **Evidence model** (`model.py`) — the mandatory distinction between *detector absent*,
  *exists but did not run*, *ran clean*, *ran without evidence*, and *ran and found*.
  `UNKNOWN` is never promoted to `VERIFIED`.
- **Change impact** (`impact.py`) — DIRECT / INDIRECT / POSSIBLE / NO_KNOWN_IMPACT, with
  focused test selection that states *why* each test was chosen.
- **Recurrence memory** (`registry.py`) — NEW / STILL_OPEN / **RECURRED** / RESOLVED.
  A detector that did not run can never resolve a finding.
- **AI boundary** (`ai_boundary.py`) — contract only, no provider. Nine decisions are
  permanently reserved from AI, enforced by `AdapterViolation`.

## 4. Rules

| Rule | Severity | Detects |
|---|---|---|
| `GULA-MIG-001` | P0 | Duplicate Alembic revision id (silently unreachable migration) |
| `GULA-MIG-002` | P0 | Alembic graph without exactly one head |
| `GULA-ARCH-001` | P1 | Physical table mapped by more than one app package |
| `GULA-STATE-001` | P1 | Duplicate key within one state-transition dict |
| `GULA-SCHEMA-001` | P0 | Foreign key whose type family differs from its target primary key |

## 5. Current output at `eb76689`

```
GULA-MIG-001     VERIFIED   101 revisions scanned
GULA-MIG-002     VERIFIED   heads=['20260908_0001']
GULA-ARCH-001    FAILED     national_facilities mapped by ['models', 'national']   (NR-006)
GULA-STATE-001   VERIFIED   3 transition tables scanned
GULA-SCHEMA-001  FAILED     pharmacy_drug_catalog.id Integer vs String(26) FKs     (NR-003)
health = BLOCKED · production_ready = false
```

`GULA-SCHEMA-001` **independently rediscovered NR-003 statically**, with no database —
a blocker originally found only by executing migrations against PostgreSQL.

## 6. Detector correctness

Two false positives were found in the engine's own first run and fixed before commit:

1. `GULA-STATE-001` pooled keys across separate dict literals in one file, reporting a
   name reused by two unrelated maps as a collision. Now grouped per dict literal, and
   it agrees with `flake8 F601`.
2. `GULA-SCHEMA-001` flagged `varchar(64) → varchar(36)`, which PostgreSQL accepts.
   Narrowed to type-family mismatch, which is what actually makes a key unbuildable.

Both corrections are locked by tests.

## 7. Security and efficiency

Read-only by default; no subcommand mutates the repository or a database, and
`--write-state` is the sole opt-in. It is engineering tooling under `tools/`, not a
runtime service, so it adds no API surface to the application. No shell execution from
user input, no patient data touched, no network calls. Analysis is static and bounded:
no polling, no repeated full-repository passes, no AI calls.

## 7b. Development planner

`planner.py` turns a set of changed paths into a reviewable plan: affected components,
direct and indirect dependencies, required and optional tests, evidence required,
migration/security/clinical-safety implications, open blockers, architecture decisions,
and a minimum safe change boundary.

Risk is `LOW` / `MODERATE` / `HIGH` / `CRITICAL`, derived from **explicit factors that
are reported alongside the score**, so the classification can be argued with rather than
trusted. A migration change is `CRITICAL` and demands a clean-database proof; a change to
the shared clinical guard is `HIGH` and pulls in safety and security implications.

The planner never emits "safe to deploy" — a test enforces that.

## 8. Limits

- Five rules only. The long detector list in the brief is **NOT STARTED**, not clean.
- Impact mapping covers migrations, Blood Bank, shared clinical, tests, docs and tooling;
  everything else is deliberately `POSSIBLE_IMPACT`, never "safe".
- Contract drift (§B) is not implemented here; `zero_drift_engine.py` covers the
  frontend↔backend axis and was not duplicated.
- Health is `BLOCKED` while any blocker finding stands, and `production_ready` is
  hard-coded `false` — NR-003 remains unresolved.
