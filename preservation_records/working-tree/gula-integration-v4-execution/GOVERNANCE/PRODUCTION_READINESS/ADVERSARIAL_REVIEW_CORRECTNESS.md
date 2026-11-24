# Adversarial Review — Correctness & Reliability (Health Core Integration)

**Document:** `GOVERNANCE/PRODUCTION_READINESS/ADVERSARIAL_REVIEW_CORRECTNESS.md`
**Reviewer role:** independent adversarial reviewer (does **not** trust implementation-agent self-reports)
**Date:** 2026-11-18
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch / HEAD observed:** `integration/gula-unification-v1` / `2827c1ff Add GitHub Actions workflow for GitHub Pages deployment`
**Scope:** `backend/app/health_core/**` and `backend/tests/health_core/**` (event semantics, FHIR R4, terminology, reliability, client integration)

---

## 0. Mandate and constraints (honest disclosure)

This review operated under a strict, governance-imposed mandate:

- **Only write target:** this report file. Scratch reproduction scripts were written **only** under `/tmp/opencode/prodready/review_correctness/`.
- **All repository source, tests, config and other reports: read-only.** No fixes, commits, staging, reset, clean, DDL, DB, route activation, secret handling or production activation were performed.
- **No source file was modified.** `git status` was observed to contain many pre-existing concurrent uncommitted changes/renames; none were touched, staged or cleaned by this review.
- **Every finding below was independently reproduced** by executing real code with real in-memory service wiring. Self-reported test counts and "all events validate" claims were treated as unverified until re-run here.

**Consequence for every finding:** *Authorized to fix: NO.* All findings are **governance-blocked from remediation under this review mandate** — source modification requires a separately authorized implementation agent and a fresh verification cycle. Recommended fixes are supplied for that authorized agent.

---

## 1. Method and exact commands

Interpreter (mandated): `/tmp/opencode/mpi-venv/bin/python`. All runs from `backend/`.

### 1.1 Baseline suite (independent re-run, not a self-report)

```
$ cd /home/samertts/workspace/projects/gula-integration/backend
$ ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
    /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core -q --tb=short
```
Result (tail):
```
tests/health_core/test_terminology_validators.py ....................... [ 91%]
.................................................................        [100%]

=============================== warnings summary ===============================
.../site-packages/fastapi/testclient.py:1
  .../fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with
  `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 750 passed, 1 warning in 8.36s ========================
```
**750 passed, 0 failed, 1 unrelated deprecation warning.** The existing suite is green; the defects below survive it because the suite does not exercise the specific paths used in the reproductions.

### 1.2 Adversarial scratch reproductions (event + reliability)

```
$ ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
    /tmp/opencode/mpi-venv/bin/python -m pytest \
    /tmp/opencode/prodready/review_correctness/test_adversarial_events.py \
    /tmp/opencode/prodready/review_correctness/test_adversarial_reliability.py \
    -q --tb=short -s
```
Exact output:
```
ADMITTED PAYLOAD KEYS: ['encounter_ref', 'from_status', 'patient_ref', 'tenant_id', 'to_status', 'transition', 'version']
VALIDATION ERROR: encounter.admitted missing payload keys: ['facility_ref']
.NON-VALIDATING REAL EVENTS: [(<EventType.ENCOUNTER_ADMITTED: 'encounter.admitted'>, "encounter.admitted missing payload keys: ['facility_ref']"), (<EventType.ENCOUNTER_TRANSFERRED: 'encounter.transferred'>, "encounter.transferred missing payload keys: ['from_facility_ref', 'to_facility_ref']"), (<EventType.ENCOUNTER_ADMITTED: 'encounter.admitted'>, "encounter.admitted missing payload keys: ['facility_ref']"), (<EventType.ENCOUNTER_DISCHARGED: 'encounter.discharged'>, "encounter.discharged missing payload keys: ['disposition']")]
.STATIC: validate_domain_event absent from all production emitters
.WAL truncated 3->2; restored keys: ['SYN-KEY-0001', 'SYN-KEY-0002']
.MIDDLE DROP detected: ChecksumMismatchError WAL record sequence is not contiguous
.AFTER TAIL DELETE log.verify(): AuditVerification(ok=True, verified_count=2, failure=None, detail='chain verified')
EXTERNAL HEAD/COUNT CHECK: AuditVerification(ok=False, verified_count=2, failure=<AuditFailure.COUNT_MISMATCH: 'count_mismatch'>, detail='expected 3 records, found 2')
.STORE ACCEPTED non-SYN key; data: {'12345678901': {'v': 1}}
.
7 passed in 0.48s
```

### 1.3 Adversarial scratch reproductions (FHIR / terminology / client integration)

```
$ ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
    /tmp/opencode/mpi-venv/bin/python -m pytest \
    /tmp/opencode/prodready/review_correctness/test_adversarial_fhir_ci.py \
    -q --tb=short -s
```
Exact output:
```
BASE WEB errors: ()
CUSTOM WEB errors: ()
.TENANT_MISMATCH -> denied
DUPLICATE_ENTITY -> duplicate
INVALID_STATE_TRANSITION -> invariant
.ICD Z99.9: UNVERIFIED
LOINC 1234-5: UNVERIFIED
UCUM bPM: INVALID
.
3 passed in 0.43s
```

### 1.4 Static scans (placeholders / weakened assertions)

```
$ grep -R -n -E 'TODO|FIXME|NotImplementedError|\bpass\b|pytest.mark.skip|pytest.mark.xfail' \
    backend/app/health_core backend/tests/health_core
```
Result: **no** `TODO`, `FIXME`, `NotImplementedError`, `pytest.skip`, `pytest.xfail`, `@pytest.mark.skip` or `@pytest.mark.xfail` in production or test code. Two incidental matches are prose in docstrings (`observations.py:222` "in this pass", `fhir/support.py:10` "All values pass") — not placeholders.

### 1.5 Authoritative external verification (FHIR R4)

Fetched `https://hl7.org/fhir/R4/valueset-diagnostic-report-status.html` (FHIR v4.0.1). The `DiagnosticReportStatus` value set expansion contains **`corrected`** ("Subsequent to being final, the report has been modified to correct an error in the report or referenced results"), alongside `registered`, `partial`, `preliminary`, `final`, `amended`, `appended`, `cancelled`, `entered-in-error`, `unknown`. This is used in §4 to classify the `status="corrected"` emission as **valid**, not a defect.

---

## 2. Severity summary

| ID | Severity | Area | Title | Fix authorized? |
|---|----------|------|-------|-----------------|
| F-01 | **HIGH** | Event semantics | Catalogue validator is never invoked at emission; real encounter lifecycle events are catalogue-invalid | No — governance-blocked |
| F-02 | **MEDIUM** | Reliability / WAL | Tail-truncated but re-checksummed WAL replays silently (no terminal anchor) | No — governance-blocked |
| F-03 | **MEDIUM** | Reliability / Audit | `AuditLog.verify()` is self-referential and cannot detect tail deletion | No — governance-blocked |
| F-04 | **MEDIUM** | Client integration | `validate_all_manifests()` silently ignores its `observations` argument | No — governance-blocked |
| F-05 | **LOW** | Reliability / store | `_check_key()` accepts any non-empty string despite "synthetic reference" contract | No — governance-blocked |

**Totals: 0 CRITICAL, 1 HIGH, 3 MEDIUM, 1 LOW, 0 INFORMATIONAL defects.** Honest design limitations that are *documented* rather than defective are enumerated in §4 and are **not** counted as findings.

---

## 3. Detailed findings

### F-01 — HIGH — Event catalogue validation never enforced; real emitted events violate their own catalogue

**Exact locations**
- `backend/app/health_core/clinical/services.py:132–149` — `_ClinicalService._emit()` builds and appends a `DomainEvent` but **never calls** `validate_domain_event()`.
- `backend/app/health_core/clinical/services.py:560–574` — `EncounterService.transition()` payload for all six lifecycle event types contains only `encounter_ref`, `tenant_id`, `patient_ref`, `transition`, `from_status`, `to_status`, `version`.
- `backend/app/health_core/contracts/events.py:93–116` — catalogue definitions require fields the emitter never supplies:
  - `ENCOUNTER_ADMITTED` → `facility_ref` (line 96)
  - `ENCOUNTER_TRANSFERRED` → `from_facility_ref`, `to_facility_ref` (line 102)
  - `ENCOUNTER_DISCHARGED` → `disposition` (line 108)
  - `ENCOUNTER_CANCELLED` → `reason` (line 114)
- `backend/app/health_core/contracts/events.py:244–271` — `validate_domain_event()` is defined but, per a whole-package grep, appears in production code **only** as a definition/export (`contracts/events.py:36,244`, `contracts/__init__.py:38,118`) and is **never called** by any emitter.

**Reproduction** — `test_adversarial_events.py::test_real_admitted_event_violates_catalogue`, `::test_real_lifecycle_events_all_fail_catalogue`, `::test_production_emitters_never_call_validate_domain_event`. Real `ClinicalContext` wiring, real services, `SYN-` ids only; transitions `PLANNED→IN_PROGRESS→ADMITTED→TRANSFERRED→ADMITTED→DISCHARGED`. Output (§1.2): `encounter.admitted missing payload keys: ['facility_ref']`; `encounter.transferred missing payload keys: ['from_facility_ref', 'to_facility_ref']`; `encounter.discharged missing payload keys: ['disposition']`; static probe: validator absent from all emitters.

**Why the existing suite misses it** — `tests/health_core/test_event_semantics.py:353–361` (`test_all_real_clinical_events_validate_against_catalogue`, `len(events) == 9`) only exercises `IN_PROGRESS` (started) and `DIAGNOSIS_RESOLVED`, whose payloads happen to satisfy the catalogue. The four other legal transition targets are never emitted in that fixture, so the "all events validate" claim is **false in general** even though the test passes.

**Impact** — The event contract catalogue is decorative. A consumer that relies on `validate_domain_event()` to admit events would reject 4 of 6 real encounter lifecycle transitions; because nothing calls the validator, the events are emitted with payloads that do not meet their declared schema. This is a genuine producer/contract mismatch in a package whose stated purpose is producer–consumer conformance, and it gives false assurance via a green conformance test.

**Recommended fix (for authorized agent)** — Either (a) call `validate_domain_event(event)` inside `_emit()` before `self._events.append(event)` and complete the four payloads in `EncounterService.transition()` from the encounter/facility context, or (b) if the minimal payload is intentional, correct `EVENT_CATALOGUE` definitions to the actual emitted keys and document the rationale. Then extend the conformance fixture to exercise all six transition targets (and CANCELLED). Note this changes the pinned event count assumptions in `test_cross_module_conformance.py` and must be verified against those gates.

**Status:** governance-blocked — review-only mandate; no source changes authorized.

---

### F-02 — MEDIUM — WAL tail truncation replays silently (no terminal record/count anchor)

**Exact locations**
- `backend/app/health_core/reliability/durable.py:210–228` — `wal_bytes()` envelope contains only `schema`, `base_sequence`, `records`, `checksum`; there is no record count, last-sequence or terminal marker bound into the envelope beyond the records actually present.
- `backend/app/health_core/reliability/durable.py:245–280` — `_replay_wal()` verifies the envelope checksum, per-record checksums and contiguity from `base_sequence + 1`, but a prefix of the original record list with a freshly recomputed (unkeyed) checksum is indistinguishable from a legitimate shorter WAL.

**Reproduction** — `test_adversarial_reliability.py::test_wal_tail_truncation_replays_silently`. Three `put()`s on a fresh store; snapshot committed at sequence 0; WAL decoded, last record dropped, envelope checksum recomputed with `sealed_envelope`, restored via `restore_from()`. Output (§1.2): `WAL truncated 3->2; restored keys: ['SYN-KEY-0001', 'SYN-KEY-0002']` — `SYN-KEY-0003` silently absent, **no exception**. Control `::test_wal_middle_record_drop_is_detected` removes a middle record and is correctly rejected (`ChecksumMismatchError ... sequence is not contiguous`), proving the gap is specific to tail truncation.

**Impact** — A checksummed WAL tail can lose its last committed write(s) without detection whenever the truncation is accompanied by a recomputed checksum. The checksum is unkeyed SHA-256, so any in-process actor can recompute it. This is a **tamper-evidence gap**, not a crash-recovery bug: an actual mid-write crash produces invalid JSON/checksum and *is* rejected — stated explicitly to avoid overstating severity. Within the isolated design, it undermines the "loses nothing that was written to the WAL" assurance against an adversarial or buggy rewriter.

**Recommended fix (for authorized agent)** — Bind an authoritative terminal anchor into the WAL envelope that is not derivable from the record list alone (e.g., a `last_sequence`/`record_count` written by a separate commit path and verified in `_replay_wal()`), or key the envelope checksum with a process-local secret. Add a regression test asserting that dropping the tail record while recomputing the checksum is rejected.

**Status:** governance-blocked — review-only mandate; no source changes authorized.

---

### F-03 — MEDIUM — `AuditLog.verify()` is self-referential; tail deletion is invisible

**Exact locations**
- `backend/app/health_core/reliability/audit.py:141` — docstring claims "trusted in-process head".
- `backend/app/health_core/reliability/audit.py:151–159` — `head` and `count` are derived from `self._records` (`chain_head(self._records)`, `len(self._records)`).
- `backend/app/health_core/reliability/audit.py:194–198` — `verify()` passes `expected_head=self.head, expected_count=self.count`, i.e. the expectations are computed from the very records being verified.
- `backend/app/health_core/reliability/audit.py:84–137` — `verify_chain()` *does* detect the deletion when an external head/count is supplied (lines 91–96, 133–134).

**Reproduction** — `test_adversarial_reliability.py::test_audit_log_verify_cannot_detect_tail_deletion`. Append 3 records, capture head/count, `log._records.pop()`, then `log.verify()`. Output (§1.2): `AuditVerification(ok=True, verified_count=2, failure=None, detail='chain verified')` — the truncated log verifies cleanly. The external check returns `ok=False`, `failure=COUNT_MISMATCH`, `expected 3 records, found 2`.

**Impact** — `verify()` provides no protection against tail deletion by an actor with in-process access to the record list: both the expected head and count move with the mutation. The only sound verification path is `verify_chain()` with a head/count captured *before* the mutation — an external trust anchor this in-memory design does not itself maintain. The API claim of a "trusted in-process head" is therefore misleading. Severity is bounded by the isolated design (no durable store, no remote replica), hence MEDIUM rather than HIGH.

**Recommended fix (for authorized agent)** — Maintain an append-only, independently-updated head/count (and ideally a running index) that `append()` updates but `verify()` treats as external to `_records`, or deprecate `verify()` in favour of requiring callers to pass a previously captured `expected_head`/`expected_count` to `verify_chain()`. Correct the docstring so it no longer calls the derived head "trusted". Add a regression test for tail deletion against `verify()`.

**Status:** governance-blocked — review-only mandate; no source changes authorized.

---

### F-04 — MEDIUM — `validate_all_manifests()` silently ignores its `observations` argument

**Exact location**
- `backend/app/health_core/client_integration/validators.py:305–332` — `validate_all_manifests(manifests, observations, *, repo_root)`. Line 316 calls `validate_manifest(manifest, repo_root=repo_root)` **without** `observation=...`, so each manifest is validated against `observation_for(manifest.platform)` (the module-global `OBSERVED_CLIENTS`) rather than the caller-supplied `observations` tuple. The `observations` parameter is used only at lines 313 and 318 to build `observed_platforms` for a completeness check.

**Reproduction** — `test_adversarial_fhir_ci.py::test_validate_all_manifests_ignores_passed_observations`. Build a WEB `ClientObservation` with `project_present=False` and every layer `ABSENT`, pass it in a custom `observations` tuple, and compare to the default run. Output (§1.3): `BASE WEB errors: ()` and `CUSTOM WEB errors: ()` — the materially different observation has **no effect** on validation. A correct implementation would have produced `LAYER_STATUS_MISMATCH`, `ABSENT_PROJECT_WITH_PRESENT_LAYER`, etc.

**Impact** — Any caller that supplies scenario-specific observations (future adapters, what-if validation, test doubles) silently validates against the default filesystem observation instead. Production's default path is currently unaffected because the default `observations` equals `observation_for()`, which is why this survived the green suite. It is a latent correctness defect in a fail-closed validation engine whose contract advertises observation injection.

**Recommended fix (for authorized agent)** — Resolve the observation per manifest from the supplied tuple (with fail-closed error if absent), e.g. `obs = next(o for o in observations if o.platform is manifest.platform)` then `validate_manifest(manifest, obs, repo_root=repo_root)`. Add a regression test asserting that a custom observation changes the validation result.

**Status:** governance-blocked — review-only mandate; no source changes authorized.

---

### F-05 — LOW — `_check_key()` accepts any non-empty string despite the "synthetic reference" contract

**Exact location**
- `backend/app/health_core/reliability/durable.py:130–136` — `_check_key()` rejects non-strings and blank strings, and its error text says "store key must be a non-empty synthetic reference", but it **never calls** `is_synthetic_id()` or `reject_national_identifier()`.

**Reproduction** — `test_adversarial_reliability.py::test_store_accepts_non_synthetic_key`. `store.put("12345678901", {"v": 1})` (real-national-id-shaped, not `SYN-`) is accepted and retrievable. Output (§1.2): `STORE ACCEPTED non-SYN key; data: {'12345678901': {'v': 1}}`.

**Impact** — A real-looking identifier can enter the WAL/snapshot key space, contradicting the module's "synthetic-only" validation claim. Bounded to the in-memory sandbox (no persistence, no real patient data), hence LOW.

**Recommended fix (for authorized agent)** — Call `require_synthetic_id(key, field="key")` (from `reliability/hashing.py`) inside `_check_key()`, or document that keys are arbitrary opaque strings and remove the misleading "synthetic reference" error text and docstring claim. Add a regression test that a non-`SYN-` key is rejected.

**Status:** governance-blocked — review-only mandate; no source changes authorized.

---

## 4. Zero-finding and verified-valid areas (distinguished from defects)

The following were attacked and **did not break**. They are reported as verified-valid or as *honest, documented design limitations* — **not** as findings.

### 4.1 FHIR R4

- **`DiagnosticReport.status = "corrected"` (serializers.py:344, 363; deserializers.py:628) is VALID FHIR R4.** Verified against the HL7 FHIR v4.0.1 `diagnostic-report-status` value set (§1.5), which explicitly includes `corrected`. The suspected defect is **ruled out**.
- **Strict deserialization held.** Reference/identifier checks (`fhir/support.py:294–373`) enforce `SYN-` prefix, exact per-type prefix, `Type/SYN-...` relative form, reject display strings, absolute URLs, cross-resource type mismatches, unexpected identifier systems and real-identifier-shaped values. Adversarial malformed inputs were rejected in the existing 40-test FHIR roundtrip/validation set (§1.1).
- **OperationOutcome mapping is canonicalised and complete for all raised errors.** `fhir/errors.py:118–135` maps legacy guidance shorthands (`forbidden`→`denied`, `conflict`→`duplicate`/`invariant`, `deleted`→`not-found`, `transient`→`unavailable`) into `FHIR_R4_ISSUE_TYPES` (`:44–70`); unknown codes fall back to `processing` rather than failing open. Reproduction (§1.3): `TENANT_MISMATCH→denied`, `DUPLICATE_ENTITY→duplicate`, `INVALID_STATE_TRANSITION→invariant`, all in the R4 set. The `contracts/errors.py:59` note "no FHIR resource in this sandbox" is now stale documentation (the adapter exists) — **INFORMATIONAL documentation drift, not a correctness finding**.

### 4.2 Terminology — honest documented limitations, not defects

- `IcdValidator` uppercases before curated lookup; `UcumValidator` is deliberately case-sensitive (a case-mismatched `bPM` → `INVALID`, §1.3); structurally-valid but uncirated codes return **`UNVERIFIED`, never `VALID`** (`Z99.9` and `1234-5` → `UNVERIFIED`, §1.3).
- **LOINC check-digit recomputation is not implemented** (`terminology/validators.py:213–230`), explicitly documented as `CheckDigitStatus.NOT_VERIFIED_OFFLINE` with the reason (no authoritative algorithm/full release offline; tested mod-10 candidates disagree with inspected codes). This is an honest isolated-design limitation, **not** a silent-acceptance defect.
- The **LOINC structural-pattern mismatch** — `clinical/validation.py:23` (`^[0-9]{4,6}-[0-9]$`) vs `terminology/validators.py:38` (`^[0-9]{3,6}-[0-9]$`) — is documented in `validators.py:34–37` and in `LOINC_RELEASE.notes`. The adapter widened its pattern so its own curated 3-digit codes are self-consistent. No consumer was found that treats an UNVERIFIED code as accepted. Classified as a **documented divergence**, not a defect.

### 4.3 Reliability — controls that held

- Retry/backoff, dead-letter terminality, metrics numeric-only, backup checksum/schema/count validation, conflict strategies and the load harness were exercised by the existing 750-test suite (§1.1); no adversarial break was found in these areas.
- WAL **per-record** checksums and sequence contiguity do reject middle-record tampering (F-02 control) and raw byte truncation (invalid JSON/checksum); the gap is narrowly the re-checksummed tail.
- Hash-chain mutation, field tampering, reordering and sequence-gap detection in `verify_chain()` all function; only the self-referential `verify()` path is affected (F-03).

### 4.4 Isolation / sandbox guards

- `backend/app/health_core` constructors never import `app.factory`/`app.main`; no route, DB, broker or network activation was observed. `tests/health_core/test_sandbox_guards.py` (4 tests, §1.1) passes.
- No `TODO`, `FIXME`, `NotImplementedError`, `pytest.skip` or `pytest.xfail` anywhere in production or tests (§1.4).
- Synthetic `SYN-` ids were used exclusively in all reproductions; no real identifier or patient data was introduced.

---

## 5. Limitations of this review (stated honestly)

1. **The 750-test baseline is green.** All findings are paths the existing suite does not cover; this review extends, rather than contradicts, those tests.
2. **Scope is code-and-in-memory only.** No database, broker, HTTP server, filesystem persistence or production activation was used, as required by the mandate. Findings about "tamper evidence" and "trust anchors" concern the in-memory designs' claims, not a deployed persistence layer.
3. **`OBSERVED_CLIENTS` absence probes are scoped checks** (documented in `client_integration/observations.py:8–10`), not proof that an arbitrary alternative client implementation cannot exist. F-04 concerns argument-plumbing, not the truthfulness of those observations.
4. **No fixes were applied or verified.** Recommended fixes are proposals for an authorized implementation agent and have not been compiled, tested or regression-checked here.
5. **Concurrent uncommitted work exists** in the working tree from other sessions; this review neither caused nor altered it, and none of it was included in the reproductions beyond the read-only target files.
6. External FHIR verification was a single authoritative value-set page (FHIR v4.0.1); no other external terminology dataset was consulted (none is available offline, as the implementation itself notes).

---

## 6. Verdict

**Correctness/reliability verdict: CONDITIONAL — not certified clean.**

The Health Core integration is internally consistent and its 750-test suite passes, but independent adversarial reproduction found **one HIGH** contract-enforcement defect (F-01) and **three MEDIUM** integrity/validation defects (F-02, F-03, F-04), plus **one LOW** validation gap (F-05). The HIGH finding means the headline "all real events validate against the catalogue" conformance claim is not generally true: four legal encounter lifecycle transitions emit catalogue-invalid events, and the validator is wired to nothing in production.

None of these findings were fixable under this review's governance mandate. **Required next step:** an authorized implementation agent remediates F-01 (and F-02–F-05), extends the conformance fixtures to cover the untested lifecycle paths, and re-runs the full 750-test suite plus these adversarial reproductions before any production-readiness certification is granted.

---

*End of report. Sole authorized write target: this file. No repository source was modified.*
