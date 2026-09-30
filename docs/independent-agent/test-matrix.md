# Test matrix — what this pass verified, and how

"Proof" is reserved for a claim measured against a real artifact. Everything else
is named for what it is.

| Area | Probe | Strength | Result |
|---|---|---|---|
| SQL injection | grep for f-string / `%` interpolation inside `text()` / `execute()` over `app/` | candidate sweep; absence of a pattern, not proof of parameterisation everywhere | 0 sites |
| Unsafe deserialization | grep for `pickle.loads`, `eval(`, `exec(`, unsafe `yaml.load` | candidate sweep | 0 uses |
| Clinical integrity — Invariant #6 | read every `LabResult` write path; check the compare-and-swap | read, not executed | CAS present; no bypassing update path |
| Tenant isolation — `app/reference` | AST over route signatures + grep for the principal + served-path check | measured: AST + assembled app | 4 handlers client-scoped; package unserved |
| Tenant isolation — served surface | tenant parameters over 1794 served operations via OpenAPI | measured inventory | 70 operations; 2 verified correct, 68 unverified |
| Citizen PHI authorization | read `require_citizen_relationship` and its binding | read the effective dependency | correct |
| Environment integrity | same suite run with the database up and killed | executed, both states | 13/457/0 up; 17/370/83 killed |
| Test tripwires added | `tests/independent/test_reference_package_tenant_scope.py` | 3 tests, pass; ruff clean | IA-001 tripwired |

## Not attempted, and why

* **Distributed / offline synchronization, CRDT, Merkle, vector clocks** — the
  brief asks for conflict scenarios across two facilities. Not attempted: the
  tables those paths write are inside RB-2/RB-3, so a scenario would fail on a
  missing table and prove nothing about conflict resolution. Sequence this after
  the schema is buildable.
* **`EXPLAIN ANALYZE` performance work** — requires a populated database at
  realistic scale; the available databases are structural fixtures with ~0 rows,
  so any plan would be a seq-scan on an empty table and would mislead.
* **Chaos (Redis / RabbitMQ down)** — neither is running in this container, so
  "fails safely" could not be distinguished from "was never reached".

## RB-3 — `/ehr` surface probes (2026-09-30)

Executable probes, not pytest tests. Scripts live in the session scratchpad and
are recorded here so the numbers can be re-derived.

| probe | database | subject | result |
|---|---|---|---|
| served-surface enumeration | — | `/ehr` paths and operations in the OpenAPI schema | 54 paths / 86 operations / 86 route functions |
| head-DB execution | `gula_agent2` @ `20260916_0001`, 423 tables | all 86 operations | 85 × `500` `UndefinedTable`, 1 × `403`, **0 × 2xx** |
| physical-table check | `gula_agent2` | the 19 tables the surface needs | 0 present |
| migration search | — | any migration creating those 19 | 0; `national_patients` appears only as a guarded FK target |
| AST trace | — | route → service → model → table, all 86 | 86/86 resolve to a real model; 0 stubs |
| clinical read gate, deny paths | `gula_agent2` | `ClinicalEhrReadGate._resolve` | denies `legacy_identity_unresolved`; emits `ehr_facility_scope_unavailable` on empty/`None` facility id — 2 distinct reasons, so not a constant denial |
| clinical read gate, allow path | `gula_agent2` | can it reach `ALLOWED`? | **UNKNOWN** — needs a full identity spine; FK `niam_legacy_account_links_canonical_account_id_fkey` blocks a shortcut |
| code-path run | SQLite (scratch file) | all 86 with the 19 tables created | 8 × `200` (2 vacuously empty), 50 × `404`, 27 × `RecursionError`, 1 × harness `OperationalError` |
| IA-005 isolation | SQLite | which value recurses | only `metadata`, `type=MetaData`; 486+484 `jsonable_encoder` frames of 1052 |
| IA-005 causation | none | does a small `MetaData` recurse? | empty → encodes; **one table → recurses**. Predates NR-086 |
| IA-005 exposure | — | static, over all 86 operations | 59 exposed / 27 not |
| IA-005 prediction check | SQLite, records seeded | 2 exposed + 2 unexposed operations | 4/4 as predicted, both directions |
| IA-005 blast radius | — | tables in `SHARED_METADATA` with a `metadata` column | 124 |
| head-DB integrity after the pass | `gula_agent2` | tables / head / rows added | 423 / `20260916_0001` / 0 — unchanged |
