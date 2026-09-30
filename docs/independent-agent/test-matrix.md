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

## IA-005 — serializer regression (2026-09-30)

`backend/tests/verification/test_orm_metadata_column_serialization.py`, 13 tests,
dialect-free. Written **before** the fix.

| stage | result |
|---|---|
| baseline (unfixed) | **9 failed**, 4 passed |
| after the fix | **13 passed** |
| perturbation (`getattr(instance, col.name)` restored) | **9 failed**, 4 passed |
| restored | **13 passed** |

The 4 passing throughout are the no-collateral-change and population guards, which
must hold in both states — they are what stops the suite passing vacuously.

| wider check | result |
|---|---|
| affected models with a `to_dict()` | **119 / 119** serialise safely and JSON-encode |
| `MetaData`/`Table`/`SchemaItem` anywhere in any payload | **none** (recursive scan) |
| `/ehr` code-path probe, 86 operations (SQLite) | `RecursionError` **27 → 1**; `200` **8 → 35** |
| seeded-record probe | `RecursionError` → **200** with `metadata` = the column value |
| `tests/verification/` + `tests/independent/` | **104 passed, 145 skipped, 0 failed** |

**Dialect caveat, recorded because it limits every row above:** `tests/conftest.py:28`
forces `DATABASE_URL` to `sqlite:///:memory:`, so the backend suite is SQLite
evidence. Passing a PostgreSQL URL does not override it — it hung the run and that
run is void (ENVIRONMENT, not a code defect).

### Full backend suite, with the IA-005 fix in place

`pytest tests/ -q` — **1 failed, 2846 passed, 185 skipped** in 318 s.

The single failure is **pre-existing and not a regression from IA-005**, proven
rather than asserted:

| step | result |
|---|---|
| `tests/verification/test_single_import_path.py::test_no_module_is_loaded_under_two_names` in the full suite | **FAILED** — `backend.app.integration`, `.connectors`, `.connectors.ntfy` are loaded under both `app.*` and `backend.app.*` |
| the same test in isolation | **passes** — the failure is order-dependent, triggered by the kernel tests |
| the same reproducer with the IA-005 change **stashed** | **FAILED identically**, same three modules |
| restored | fix green, 13/13 |

So it is the NR-087 guard catching a real, order-dependent shadow introduced by
the kernel tests' dynamic connector loading — a genuine open defect in its own
right, and untouched by this change. The guard is doing its job; `KNOWN_SHADOWED`
was pinned from a single-file run, which is why a whole-suite run surfaces more.

Recorded as an **order-dependency limitation of my own guard**: pinning an exact
set measured in isolation understates what the assembled suite loads.

## IA-006 / IA-008 / IA-009 — measurement provenance (2026-09-30)

Every conformance number below states its **(code lineage, database lineage)** pair,
because R-14 showed that omitting it produces false positives at scale.

| measurement | code lineage | database | result |
|---|---|---|---|
| EHR migration absence | this lane `f538bd4f` | — (migration files) | 0 `ehr_*` creations, 0 `national_patients` creations |
| EHR migration absence | integration `ce097a0c` | — (migration files) | 0 and 0 — **INDEPENDENTLY VERIFIED** |
| `/ehr` runtime, 86 operations | this lane | `gula_agent2` | 85 × `500`, 1 × `403`, 0 × 2xx |
| 65 FKs → `national_patients`, live/dormant split | this lane | `gula_agent2` | 4 live / 61 dormant |
| pharmacy ORM↔schema drift | **this lane** | `gula_agent2` | 216/228/178 — **RETRACTED, cross-lane artefact** |
| pharmacy ORM↔schema drift | **integration `ce097a0c`** | `gula_agent2` | clean — pharmacy absent from the unwritable set |
| platform ORM↔schema conformance | integration `ce097a0c` | `gula_agent2` | 409 present / 371 absent / **26 present-but-unwritable** / 293 ORM columns absent |
| lane divergence | this lane vs `ce097a0c` | — | 176 commits, 10 migrations, every clinical domain differs |

The lab-core hosting test (`patients` 16 cols, `lab_orders` 12, `lab_results` 16,
`visits` 6, no JSON extension point) is read from the physical schema of `gula_agent2`
and is lineage-independent.

## IA-007 — invoice-number stamping (2026-09-30)

`backend/tests/verification/test_invoice_number_is_persisted.py`, 5 tests, schema-free
(a stub session replaces the absent `ins_*` tables).

| stage | result |
|---|---|
| baseline | **4 failed**, 1 passed — `TypeError: 'MetaData' object does not support item assignment` |
| after the fix | **5 passed** |
| perturbation: both identifiers back to `.metadata` | **3 failed** — `TypeError: 'MetaData' object is not iterable` |
| restored | **5 passed** |

The one test passing throughout asserts the column is mapped as `extra_metadata`; it
guards the other four from passing for the wrong reason.

Reachability, established before fixing: `generate_invoice` has no caller but
`batch_invoices`, which has none either, and `ins_claims` is absent from the head DB.
Severity corrected P1 → P3.

## IA-010 — audit-chain integrity probe (2026-09-30)

Runtime, against `gula_agent2`; every write rolled back (table verified back to 0 rows).

| probe | result |
|---|---|
| overwrite one row's `chain_hash` (UPDATE) | **refused by PostgreSQL** — `audit_logs is append-only: UPDATE operation is not permitted` |
| triggers present on `audit_logs` | `trg_audit_logs_no_update`, `trg_audit_logs_no_delete` → `audit_logs_deny_mutation()` |
| 3 rows via `log_action`, then verify | `status=intact verified=True checked=3` |
| + 1 row with `chain_hash = NULL`, then verify | `status=intact verified=True checked=4 broken=0` — **the gap** |
| existing suite coverage of the NULL case | **none** (`test_compliance_integrity.py` covers field tampering and silent deletion only) |
| is NULL legitimate? | **yes for legacy rows** — nullable since the base schema, back-filled by `20260324_0009`, so the fix needs a deployment boundary |

## IA-011 — FHIR path A contract audit (2026-09-30)

| probe | result |
|---|---|
| served `_lab_result_to_observation`, flags `H`/`L`/`N` | conformant v3-ObservationInterpretation codes |
| served builder, flags `critical`/`unknown`/`normal`/`high`/`critical_high` | passed through verbatim — **non-conformant** codes in a declared HL7 system |
| served builder, empty flag | no `interpretation` emitted (branch skipped) |
| served builder timestamps | `2026-01-01T12:00:00` — correct ISO-8601 |
| unreached `FHIRObservationMapper`, flags `H`/`L`/`critical` | all → **`N` (Normal)** |
| unreached builder, glucose 180 mg/dL vs range 70–110, flag `H` | emitted as **interpretation Normal**, LOINC code `""`, `issued` `2026-01-01 12:00:00` |
| `lab_results.test_code` exists? | **no** — the column is on `test_types` |
| `FHIRObservationMapper` production callers | **none** — 2 re-exports, 1 unit test |
| `lab_results.flag` writers | 4 disagreeing vocabularies, no enum, no validation |

## national_patients / IA-004 / IA-012 (2026-09-30)

All runtime probes against `gula_agent2`; nothing written (all tables held 0 rows before
and after).

| probe | lineage | result |
|---|---|---|
| FK columns naming `national_patients`, live vs dormant | this lane | 4 live / 61 dormant, 63 of 65 NOT NULL |
| physical FK target of the 3 pharmacy `patient_id` columns | — | all → `patients.id`, type `INTEGER` |
| pharmacy route request schema | **integration `ce097a0c`** | `patient_id: int \| None` — **coherent with the column; NO DEFECT FOUND** |
| pharmacy route request schema | this lane | `patient_id: str` — cross-lane staleness (IA-008) |
| `filter(DispenseRecord.patient_id == "5")` | integration | OK, 0 rows (assignment cast) |
| `filter(... == "01ARZ…")` | integration | **`DataError: invalid input syntax for type integer`** → IA-012 |
| `filter(... == 5)` | integration | OK, 0 rows |
| served OpenAPI type of that path param | integration | `('patient_id', 'string')` — served, and wrong |
| `niam_citizen_relationships` FK constraints | — | `…_person (citizen_id → niam_persons)` **present**; `patient_id` has **no FK** |
| `20260914_0001_citizen_relationship_person_fk.py` present? | integration **yes**, this lane **no** | IA-004 `citizen_id` arm closed only in the shipping lineage |

## IA-013 — kernel event bus delivery guarantees (2026-09-30)

In-process probe, no database.

| probe | result |
|---|---|
| 5 × `publish("probe.ok")` | handler invoked 5× |
| 1 × `publish("probe.fail")`, handler raises | handler invoked; exception swallowed into a log line |
| failed event in `retry_queue` | **0** |
| failed event in `dead_letter_queue` | **0** |
| `outbox._messages` after 6 publishes | **0** — `publish` never enqueues |
| `inbox` entries | **0** |
| `EventStore.count()` after 6 / after 506 | 6 / **506** — unbounded, never evicted |
| publishers found | 8+: plugin API, SDK, and 6 national services |
| `search_platform` tables present? | **yes** (`national_search_results`, `national_search_saved_searches`) → a live publisher |
| subscribers found | `identity/events.py` ×3 (`person.created`, `account.created`, `identity.verified`), `health_data/streaming/pipeline.py` |
| durable alternative exists? | **yes** — `outbox_service.py` over the present `outbox_events`, with `OutboxWorker` started in two places |
