# GULA Master Negative Register

**Generated:** 2026-09-08 · **Head:** `604b245` · **production_ready:** `false`
**Machine-readable companion:** [`GULA_MASTER_NEGATIVE_REGISTER.json`](./GULA_MASTER_NEGATIVE_REGISTER.json)
**Remediation plan:** [`GULA_MASTER_REMEDIATION_PLAN.md`](./GULA_MASTER_REMEDIATION_PLAN.md)

## 0. How to read this register (integrity statement)

This is a **first evidence-driven pass**, not a completed audit.

Every finding below is backed by something that was **actually executed or read** in this
session. Nothing was inferred from plausibility. Where evidence is weak, the finding says so.

> **Absence of a finding in a category does NOT mean that category is clean.**
> The majority of the 123 requested risk categories were **not audited**. See
> §7 Audit Coverage Matrix and finding **NR-013**. Treat unaudited categories as
> _unknown risk_, never as _no risk_.

Existing architecture standards were **linked, not duplicated** — see
`CANONICAL_ARCHITECTURE.md`, `ARCHITECTURE_RULES_PROGRAM_CONSTITUTION_001.md`,
`MODULE_DEPENDENCY_MATRIX.md`, `ENTITY_CATALOG.md`, `DEPENDENCY_APPROVAL_POLICY.md`,
and `docs/adr/`.

## 1. Summary

| Severity  | Count | Fixed | Open |
| --------- | ----- | ----- | ---- |
| P0        | 10     | 6     | 4    |
| P1        | 21     | 11     | 10    |
| P2        | 20     | 5     | 15    |
| P3        | 7     | 1     | 6    |
| **Total** | **58** | **23** | **35** |

_Fixed counts only rows whose status begins FIXED. AUTH-005's finalization
re-graded NR-038 and NR-043 to PARTIALLY VERIFIED after NR-044 showed the code
paths they harden cannot execute, so the fixed total moves down by two while the
work itself stands. NR-044.1 has since converted the repositories and the actor
dependency, which makes the `/niam/*` gate executable; it does not make the
route handlers executable, so neither finding may be re-graded yet — that needs
NR-044.2 and NR-044.3._

_NR-044.1's final verification added NR-045 and NR-046. Both were found by
running the converted path against the migrated schema rather than by reading
it, and neither is caused by the conversion: NR-045 is a v2 audit writer that
was never exercised against real columns, NR-046 is a predicate that both
pre-conversion dependencies also omitted. NR-045 is why NR-044.1 is PARTIALLY
VERIFIED rather than VERIFIED — the authorization allow path cannot be
exercised while every gateway request answers 503._

_NR-045 has since been repaired and verified. The gateway's DENY path is now
proven end to end: 403 with the denial recorded and hash-chained. Attempting the
ALLOW proof with a fully authorized fixture then surfaced **NR-047** — the
`Organization` ORM does not match its table, so the operational-scope lookup
raises `UndefinedColumn` and the resolver reports it as `invalid_context`.
NR-044.1 therefore stays PARTIALLY VERIFIED, with a different and more precisely
located blocker than before._

_NR-047 is now repaired and verified, and the clinical ALLOW path returns 200.
**NR-044.2** then converted `identity/services`, `identity/api`,
`identity/policy_engine.py` and `services/clinical_scope_bridge_service.py` to
the synchronous Session and deleted `SyncSessionAsyncFacade`, dropping the
unreachable-async ledger from 40 modules to 20. It added **NR-048** (the gateway
reported any internal fault as an authorization denial — the mechanism that hid
NR-047, now fixed) and **NR-049** (the ledger's own owner rule could not see a
module that named its session `self._session`, so one had been invisible since
the ledger was written; the rule is fixed, the module is NR-044.3's to convert)._

_**NR-044.3** then converted what was left and both were re-graded on evidence.
It also surfaced **NR-052**: the gate deciding who may assert an assurance
profile for another account filtered on a column that does not exist, so it had
never evaluated — a control that failed closed by crashing. That is the third
finding in this sequence (with NR-045 and NR-048) that was invisible purely
because the code could not run._

_**NR-050 discovery** then measured the capability tree properly and corrected
this register: the earlier "all ten fail to import" was measured with the wrong
`sys.path` and a four-module sample. One package is complete and live, nine are a
single character from importable, and all three defect classes come from one
generator that is still emitting them (**NR-053**). Nine of the nine also have
shipped frontend routes pointing at unregistered endpoints (**NR-054**)._

_**PROGRAM-EXT-001** then established the extensibility foundation on top of the
registry that already loads, rather than building a second one. It added
**NR-050** (the `app/capabilities/` tree is 268 files of scaffolding that cannot
import) and **NR-051** (six reusable concepts with no canonical owner). Both are
decisions, not patches, and both are listed in the decisions table below._

_Counts are generated from the JSON companion; the table above had drifted
since the first pass and now reflects all findings, not one session's._

**Single true deployment blocker today:** **NR-003** — pharmacy primary-key type divergence.

## 2. Findings index

| ID     | Sev | Domain              | Title | Status |
| ------ | --- | ------------------- | ----- | ------ |
| NR-001 | P0  | Platform/Alembic | Duplicate revision id made `clinical_command_receipts` unreachable | FIXED — VERIFIED |
| NR-002 | P0  | Platform/Alembic | Three unmerged heads made clean deployment impossible | FIXED — VERIFIED |
| NR-003 | P0  | Pharmacy | PK type divergence blocks any full `upgrade head` | OPEN — BLOCKED / DECISION REQUIRED |
| NR-004 | P1  | Blood Bank | Shared transition table shadowed the blood-unit `reserved` state | FIXED — VERIFIED |
| NR-005 | P1  | Platform/Alembic | Unguarded duplicate index could never succeed | FIXED — VERIFIED |
| NR-006 | P1  | National + Core | `national_facilities` mapped by two ORM classes | FIXED — VERIFIED (second mapper retired to a bare FK anchor) |
| NR-007 | P1  | Clinical/Blood Bank | State machine is entity-agnostic by construction | PARTIALLY RESOLVED — 4 collisions attributed; 28 ... |
| NR-008 | P2  | Platform | `signxml` missing from lock file | OPEN — NOT A PRODUCTION BLOCKER |
| NR-009 | P2  | Platform CI | Artifact quota exhausted; evidence jobs all red | OPEN — EXTERNAL |
| NR-010 | P2  | Platform CI | `if:always()` upload masks the true failing step | OPEN |
| NR-011 | P2  | frontend-v3 | Mobile nav accessible name contradicts its test | OPEN |
| NR-012 | P2  | Clinical | Replay returns deterministic 409, not original response | ACCEPTED DESIGN — VERIFIED |
| NR-013 | P3  | Platform | Audit coverage is narrow | NOT STARTED |
| NR-014 | P3  | Platform | No verified national capacity numbers | NOT STARTED — GAP |
| NR-015 | P3  | Platform CI | Postgres auth failure in migration gate | OPEN — LOW EVIDENCE |
| NR-016 | P1  | Platform CI | Changed-files quality gate reported PASS when MyPy failed to execute | FIXED — VERIFIED |
| NR-017 | P2  | Pharmacy | Warehouse is modelled in the schema but implemented nowhere | OPEN — ARCHITECTURE DECISION REQUIRED |
| NR-018 | P1  | Platform Migrations | Ten declarative bases were invisible to autogenerate | PARTIALLY VERIFIED — 2 of 8 bases zero-diff capab... |
| NR-019 | P1  | AI Platform | Importing `app.ai` wrote to the database at import time | FIXED — VERIFIED |
| NR-020 | P0  | Blood Bank | Transfusion state machine had no `verified` state | FIXED — VERIFIED |
| NR-021 | P0  | Blood Bank | Inventory and component endpoints ignored `lab_id` | FIXED — VERIFIED |
| NR-022 | P0  | National Core | Four of the five most-depended-on tables do not exist | OPEN — ARCHITECTURE DECISION REQUIRED |
| NR-023 | P0  | Platform Migrations | Autogenerate cannot run: foreign keys cross `MetaData` boundaries | OPEN — BLOCKED BY NR-030 (NR-006 cleared) |
| NR-024 | P3  | Platform Migrations | `CitizenPlatformBase` is registered but maps zero tables | OPEN — LOW SEVERITY |
| NR-025 | P2  | Platform-wide | One name, two identifier schemes: `_ulid()` is a real ULID twice, a truncated UUID4 twelve times (thirteen before BATCH-3) | OPEN — DESIGN DEFECT |
| NR-026 | P0  | Nursing Platform | Entire Nursing ORM diverges from its schema; every model fails on a plain SELECT | FIXED — VERIFIED (BATCH-3; 15/15 models SELECT, 0 destructive diff, no migration) |
| NR-027 | P1  | Blood Bank | No Blood Bank mutation writes an audit log entry | PARTIALLY VERIFIED — canonical paths audited; 7 l... |
| NR-028 | P3  | Platform-wide | Ambiguous package root: 130 imports say `backend.app`, the rest say `app` | OPEN — CONFIRMED |
| NR-029 | P1  | Identity Platform | Three foreign keys named the ORM class instead of its table | FIXED — VERIFIED |
| NR-030 | P1  | Platform Migrations | Twelve physical tables are mapped by no ORM class | PARTIALLY VERIFIED — all 12 classified and named |
| NR-031 | P1  | Blood Bank | `POST /samples/{id}/transition` required an Idempotency-Key and discarded it | FIXED — VERIFIED |
| NR-032 | P0  | Medication (platform-wide) | Nine modules across five domains depend on `ehr_medication_*`; zero `ehr_*` tables exist | OPEN — OWNERSHIP DECIDED (BATCH-3.1), EXECUTION NEEDS APPROVAL |
| NR-033 | P2  | Nursing Platform | The eight `/nursing/coordination/*` endpoints persist nothing — audit entry only, no table | OPEN — ALL EIGHT CLASSIFIED (BATCH-3.1) |
| NR-034 | P0  | Pharmacy | A point-of-sale sale naming a patient writes an EHR `MedicationDispense` and cannot commit | FIXED — VERIFIED (MED-001) |
| NR-035 | P1  | Identity Platform | The `user_id` token claim is ambiguous across `users` and `lab_users` | FIXED — VERIFIED (AUTH-003; `act` discriminator, single fail-closed resolver) |
| NR-036 | P1  | Platform-wide | The test schema is built from ORM metadata, so tests pass against tables no migration creates | FIXED — VERIFIED (TEST-001 + TEST-001.1; gate binding in CI) |
| NR-037 | P1  | Identity Platform | Assurance was one scale across four independent verification purposes | FIXED — VERIFIED (AUTH-004; purpose-scoped profile, ADR-026) |
| NR-038 | P1  | Identity Platform | The client supplies its own identity assurance level, assessor and evidence | **FIXED — VERIFIED** (NR-044.3). Proved behaviourally at last: no verification record → floor assurance; only a record written through the real state machine raises it; the overall is the weakest axis, so authentication strength cannot lift an unproofed identity; acting for another account is refused with 403 |
| NR-039 | P1  | Identity Platform | `users.is_verified` means both "a code was received" and "identity confirmed" | FIXED — VERIFIED (AUTH-005; linkage requires identity L2) |
| NR-040 | P2  | Identity Platform | The canonical verification domain had a reader and no writer | FIXED — VERIFIED (AUTH-005; VerificationWorkflow) |
| NR-041 | P2  | Identity Platform | MFA exists for staff only, and its service takes an undiscriminated integer id | OPEN |
| NR-042 | P3  | National Platform | The declared biometrics table points at raw biometric data | OPEN — DO NOT BUILD |
| NR-043 | P2  | Identity Platform | Workspace eligibility ignored the organization's own standing | **FIXED — VERIFIED** (NR-044.3). Deactivating the organization removes its workspace from an active representative's eligible set; suspending it does too. One fact changes between assertions, so the predicate is what is proved. AUTH-F5's open half (should membership confer eligibility?) is a policy decision and unchanged |
| NR-044 | P1  | Identity Platform | The NIAM async service layer cannot execute — there is no async engine | **RESOLVED for every reachable path** — .1, .2 and .3 all VERIFIED. Ledger 50 → 40 → 20 → **4**, and the four that remain are inside the dead `app/capabilities/` tree (NR-050), unreachable twice over. One Class B coroutine is preserved deliberately: `test_fhir_connection` makes a real httpx call, and only its database work was converted |
| NR-045 | P1  | Clinical Gateway | `CanonicalAuditService` cannot write a row, so every clinical-gateway request answers 503 | **VERIFIED** — `IdentityAuditEntry.uuid` now carries the canonical default; the gateway answers 403 where it answered 503 and the denial is readable in `niam_audit_entries` with a valid hash chain. No migration, no constraint weakened |
| NR-047 | P1  | Operational models | The `Organization` ORM does not match the `organizations` table | **VERIFIED** — `org_id`/`org_type` mapped onto the existing `organization_id`/`organization_type`; `updated_at` removed from the ORM (read by nothing) rather than added; only `parent_org_id` added, by additive migration `20260913_0001`. Bootstrap now completes and is idempotent for organizations; the clinical ALLOW path returns **200** |
| NR-046 | P2  | Identity Platform | The NIAM actor dependency does not consult `UserSession.expires_at` | OPEN — pre-existing, not a NR-044.1 regression; bounded by the access token's own enforced `exp` |
| NR-048 | P1  | Clinical Gateway | The gateway reported any internal fault as an authorization denial | **VERIFIED** (NR-044.2) — `except Exception → invalid_context` narrowed to the context service's own denial vocabulary. This is how NR-047's `UndefinedColumn` reached clients as a 403 and was written into the audit chain as a decision nobody made |
| NR-049 | P2  | Identity Platform | The NR-044 ledger could not see a module that stored its session as `self._session` | OPEN (module) / FIXED (guard) — widening the owner rule raised the ledger from 19 to 20 and surfaced `reference/infrastructure/repositories.py`, invisible for as long as the ledger has existed. Converting it belongs to NR-044.3 |
| NR-050 | P2  | Platform / Capabilities | Nine of ten packages under `app/capabilities/` cannot import, and nine have live frontend routes | **DISCOVERY COMPLETE — DECISION REQUIRED** (recommendation: SPLIT). Corrects the earlier entry: measured in the real environment over all 267 modules, `fhir_interoperability` imports 27/27 and is fully live; the other nine fail on **one character each**. They are not orphans — frontend-v3 ships nine routes, nine pages and nine nav entries for them, gated on `dashboard:read`, calling endpoints `factory.py` never registers |
| NR-053 | P2  | Platform / Engineering | The capability generator still emits all three defects that made nine packages unimportable | **FIXED — VERIFIED**. Six edits; proved by generating into a temp directory and importing the result, not by grepping the generator. Four negative proofs. The ten existing packages were deliberately left alone — their disposition is still NR-050's |
| NR-055 | P2  | Platform / Engineering | The routes template built Python function names from the hyphenated URL prefix | **FIXED — VERIFIED** (NR-053). `async def list_clinical-foundation(` — a SyntaxError in every generated routes.py with a multi-word name. Invisible until someone ran the generator: the shipped files were hand-corrected and the template never was |
| NR-054 | P2  | Frontend / Platform | Nine frontend routes call capability endpoints that are never registered | **FIXED — VERIFIED**. `encounter-management` bound to its canonical owner `GET /national-data/encounters` (registered, lab-scoped, `patients:read`); the other eight removed from the router and NAV_ITEMS, components preserved and documented. Registering the existing stubs was rejected: they return a literal `{items: [], total: 0}`, which would replace a visible 404 with an invisible lie |
| NR-052 | P1  | Identity Platform | The assurance-profile administrator gate filtered on a column that does not exist | **VERIFIED** (NR-044.3) — `Assignment.account_id` is not a column, so the gate raised `AttributeError` rather than deciding. It failed closed, as a 500, and had never once been evaluated: NR-044 meant the route could not run. Now joins account → identity → person |
| NR-051 | P2  | Platform / Capabilities | Six reusable concepts have 2–4 implementations and no canonical owner | OPEN — **DECISION REQUIRED**. Notification ×4, document ×3+1 dead, workflow ×3+1 dead, consent ×3+1 dead, audit ×3 writers, terminology ×2 same-named classes. *Reuse Before Build* cannot be followed while nothing says what to reuse |
| NR-057 | P2  | Frontend / Platform | Thirty further frontend calls resolve to no registered backend route | OPEN. Same defect class as NR-054 in other domains — /niam/* ×15, /citizen-platform/* ×6, /certification/* ×2 and 7 singletons. Held by a ledger in the NR-054 contract guard that may shrink but never grow |
| NR-058 | P1  | Platform / Runtime | A real application start loads a second copy of the application through the `backend.app` root | OPEN — **PARTIALLY MITIGATED**. `create_app()` loaded 36 shadow modules including a second kernel, config, `Base` and `Engine`; `a is b` is False with identical `__file__`. NR-050 repaired the capability share (36 → 34, second kernel gone). Residual is `national/task_engine` + `workflow_runtime`; root cause is `Dockerfile:24-26` copying the app twice |
| NR-056 | P3  | Platform / Engineering | Seventeen generator modules and the engineering CLI resolved only from the repository root | **FIXED — VERIFIED**. 44 imports across 18 files. `backend/` has no `__init__.py` and the distribution publishes `app*`, so `backend.app.` only ever resolved because conftest and CI put the repo root on `sys.path`. Eighteen of nineteen modules failed to import before; all nineteen import now, and the CLI reads all 52 registry descriptors. Guarded by AST package discovery, so a future generator is covered without editing the test |

Full per-finding detail (root cause, all impact axes, minimal safe fix, acceptance
criteria, regression risk, owner, wave) is in the JSON companion.

## 3. The most important discovery

**NR-001 was far wider than Blood Bank.** `ClinicalCommandGuard` — and therefore the
`clinical_command_receipts` table that never existed — is used by **eight domains**:

```
blood_bank · pharmacy · radiology · lims · ems · critical_care · clinical · routes
```

So the shadowed migration disabled the durable idempotency claim for **every guarded
clinical command across the platform**, not only transfusion. Earlier documentation
described this as a Blood Bank issue; that understated it.

## 4. Contradiction register

| ID         | Contradiction                                                                                                                                                                                                                                                           | Evidence       | Status                                                    |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | --------------------------------------------------------- |
| C-01       | Policy "every migration must be idempotent" vs. a shipped unguarded migration                                                                                                                                                                                           | NR-005         | **VERIFIED** — resolved                                   |
| C-02       | Policy "never modify an existing migration" vs. the need to repair a migration that never ran anywhere                                                                                                                                                                  | NR-001         | **VERIFIED** — resolved on evidence that no DB applied it |
| C-03       | Pharmacy ORM uses `String(26)` ULIDs; pharmacy migrations create `Integer` ids                                                                                                                                                                                          | NR-003         | **VERIFIED** — unresolved                                 |
| C-04       | Per-entity clinical state semantics vs. one shared entity-agnostic transition table                                                                                                                                                                                     | NR-004, NR-007 | **VERIFIED** — partially resolved                         |
| C-05       | `production_ready=false` gating vs. CI that structurally cannot certify (all evidence jobs fail at upload)                                                                                                                                                              | NR-009         | **VERIFIED**                                              |
| C-06       | Domain ownership boundaries vs. two domains mapping one physical table                                                                                                                                                                                                  | NR-006         | **RESOLVED** — one owner, one table       |
| C-07       | Reproducible-build intent vs. lock file that cannot start the app                                                                                                                                                                                                       | NR-008         | **VERIFIED**                                              |
| C-08       | "National scale" ambition vs. absence of any capacity numbers                                                                                                                                                                                                           | NR-014         | **VERIFIED as a gap**                                     |
| C-09..C-20 | offline-first vs clinical authority · CRDT vs clinical truth · privacy vs emergency access · consent withdrawal vs legal retention · AI assistance vs clinical responsibility · HA vs strong consistency · green vs performance · citizen ownership vs record integrity | —              | **NOT AUDITED** — candidates only, no evidence gathered   |

## 5. Intersection register

| ID   | Change point                                                                               | Domains affected                                                                 | Evidence                                                   |
| ---- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| I-01 | `ClinicalCommandGuard` / `clinical_command_receipts`                                       | blood_bank, pharmacy, radiology, lims, ems, critical_care, clinical, routes      | grep of guard usage (8 packages)                           |
| I-02 | Alembic graph                                                                              | every domain — no schema without it                                              | NR-001/002                                                 |
| I-03 | Pharmacy id type                                                                           | pharmacy + any FK referencing pharmacy entities                                  | NR-003                                                     |
| I-04 | Blood Bank state machine                                                                   | units, orders, samples, crossmatches, transfusions, reactions (one shared table) | NR-004/007                                                 |
| I-05 | `national_facilities`                                                                      | national platform + core clinical scope + authorization scoping                  | NR-006 — RESOLVED: `NationalFacility` owns it; the national domain holds a bare FK anchor |
| I-06 | Identity change → Patient → Consent → Clinical → Lab → Pharmacy → Audit → FHIR → Analytics | all                                                                              | **NOT AUDITED** — asserted by the brief, not verified here |

**Rule:** none of I-01..I-05 may be remediated inside a single domain in isolation.

## 6. Source-of-truth / data-ownership matrix (partial)

Only rows with real evidence are filled. Everything else is explicitly unaudited.

| Domain / data                                                | Source of truth                             | Writable by                           | Consumers                                | Failure behaviour                | Status                |
| ------------------------------------------------------------ | ------------------------------------------- | ------------------------------------- | ---------------------------------------- | -------------------------------- | --------------------- |
| Clinical command idempotency claims                          | `clinical_command_receipts` (single table)  | `ClinicalCommandGuard` only           | 8 domains (I-01)                         | Guard fails closed → 409         | **VERIFIED**          |
| Blood unit lifecycle state                                   | `blood_bank_units.status` via state machine | Blood Bank routes/service under guard | traceability, reservations, issue        | Transition rejected → 422        | **VERIFIED**          |
| Blood inventory movements                                    | `blood_bank_inventory_movements`            | Blood Bank service                    | traceability, reconciliation             | Rolled back with the transaction | **VERIFIED**          |
| `national_facilities`                                        | `models.clinical_scope.NationalFacility`    | `app/models` (the national domain holds a bare `Table` as FK anchor only) | authorization scoping, national platform | Rolled back with the transaction | **RESOLVED (NR-006)** |
| Pharmacy catalog / substitution                              | Undefined — schema and ORM disagree         | n/a (cannot deploy)                   | pharmacy                                 | Migration fails                  | **BROKEN (NR-003)**   |
| Patient / MPI / National ID                                  | —                                           | —                                     | —                                        | —                                | **NOT AUDITED**       |
| Consent, provider identity, device identity, analytics, FHIR | —                                           | —                                     | —                                        | —                                | **NOT AUDITED**       |

828 mapped tables were scanned for dual ownership; exactly one conflict was found (NR-006), and it is now closed — the rule holds across all 828 with no declared exceptions, held by `backend/tests/test_canonical_table_ownership.py`.

## 7. Audit coverage matrix

| Category group                                                                              | Status                                         |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Migration safety, deployment reproducibility                                                | **AUDITED — findings NR-001/002/003/005**      |
| Clinical state machines (Blood Bank)                                                        | **AUDITED — NR-004/007**                       |
| Idempotency, concurrency, transaction boundaries, failure/retry (Blood Bank + shared guard) | **VERIFIED in Phases 14B/14B.1/14C**           |
| Authorization / IDOR (Blood Bank cross-facility only)                                       | **PARTIALLY VERIFIED** — Blood Bank paths only |
| Source-of-truth / data ownership (ORM table mapping)                                        | **AUDITED AND ENFORCED — NR-006 closed; guarded in CI** |
| Dependency reproducibility                                                                  | **AUDITED — NR-008**                           |
| CI/CD failure classification                                                                | **AUDITED — NR-009/010/015**                   |
| Frontend accessibility (one component)                                                      | **AUDITED — NR-011**                           |
| National identity / MPI / duplicate patients / newborn / deceased / proxy                   | **NOT STARTED**                                |
| Consent, break-glass, privacy, purpose-of-use                                               | **NOT STARTED**                                |
| Offline / sync / CRDT / event ordering / outbox / inbox                                     | **NOT STARTED**                                |
| FHIR / HL7 / DICOM / terminology                                                            | **NOT STARTED**                                |
| AI safety and governance                                                                    | **NOT STARTED**                                |
| Security (authn, secrets, PKI, uploads, export, insider threat)                             | **NOT STARTED**                                |
| Backup / restore / DR / failover / split-brain                                              | **NOT STARTED**                                |
| Performance, scalability, capacity, Green GULA                                              | **NOT STARTED — NR-014**                       |
| Legal, retention, portability, localization, accessibility programme-wide                   | **NOT STARTED**                                |
| Pharmacy, imaging, hospital, EMS, public health, maternal/child, vaccination domains        | **NOT STARTED** (except NR-003)                |

## 8. Offline capability matrix

**NOT STARTED.** No offline/sync behaviour was examined in this pass. Producing this
matrix requires a dedicated pass over the sync layer, and it is scheduled in the
remediation plan rather than guessed at here.

## 9. Verification / evidence gap matrix (Blood Bank — the only certified-depth domain)

| Control                                                                 | Evidence              | Result              |
| ----------------------------------------------------------------------- | --------------------- | ------------------- |
| HTTP replay idempotency (reservation, issue)                            | Phase 14B             | VERIFIED            |
| Concurrent same-key HTTP (reservation, issue)                           | Phase 14B / 14B.1     | VERIFIED            |
| Sequential + concurrent payload collision                               | Phase 14B             | VERIFIED            |
| Failure before commit (7 boundaries)                                    | Phase 14C             | VERIFIED            |
| Failure after commit / lost response                                    | Phase 14C             | VERIFIED            |
| Lifecycle E2E (reserve → trace → release)                               | Phase 14D             | VERIFIED            |
| Cross-facility IDOR                                                     | Phase 14B             | VERIFIED            |
| Schema built by migrations alone                                        | Migration remediation | VERIFIED            |
| Full `upgrade head`                                                     | —                     | **FAILED — NR-003** |
| Existing-database upgrade path                                          | —                     | **NOT VERIFIED**    |
| Contract / property-based / mutation / chaos / performance / DR restore | —                     | **NOT STARTED**     |

## 10. Decisions required (do not guess)

| Ref    | Decision                                                                     | Owner                    |
| ------ | ---------------------------------------------------------------------------- | ------------------------ |
| NR-003 | Canonical pharmacy primary-key type, then a migration strategy for 23 tables | Pharmacy + Platform/Data |
| ~~NR-006~~ | DECIDED AND APPLIED: `models.clinical_scope.NationalFacility` owns `national_facilities`; the national domain keeps a bare FK anchor, not a mapper | National + Core |
| NR-007 | Per-entity state machine keying vs. accepting union semantics                | Clinical Standards       |
| PARTIALLY RESOLVED — 4 collisions attributed; 28 ... | Whether stored-response replay is required by API clients                    | Clinical Standards + API |
| NR-014 | National capacity targets                                                    | Programme                |
