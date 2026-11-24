# WORKSTREAM D — TERMINOLOGY RELEASE VALIDATION REPORT

**Program:** GULA Production Readiness Acceleration Program
**Workstream:** WS-D (Terminology Release Validation + Provenance) — closure of WS-D finding F-04
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` · **HEAD:** `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged)
**Data class:** SYNTHETIC / OFFLINE-INSPECTED ONLY — no database, migration, DDL, network fetch,
deployment, real patient record or secret.
**Governing decision:** `GOVERNANCE/FINAL_DECISION.md` remains **HOLD** (md5 `effdfeaf10234678d83b2668c4489552`);
MPI verdict remains **REJECT** (`MPI_INDEPENDENT_AUDIT_FINDINGS.md` md5 `ea3969d09aaf7b0b28a065838b44a594`,
`MPI_FINAL_INDEPENDENT_AUDIT.md` md5 `1a02c01563c93b07a7cdb92c0462bf36`). This report is development
evidence only — not a clinical-readiness, release, safety, full-release-conformance or production-approval claim.
**Git discipline:** no commit, push, merge, rebase, PR, deploy, `git add`, `git reset` or `git clean`.
**Verification date:** 2026-11-18.

---

## 1. Scope and source findings

Reviewed first: `GOVERNANCE/ACCELERATION/QUALITY_ARCHITECTURE_REVIEW.md` §4 F-04 and
`GOVERNANCE/ACCELERATION/ACCELERATED_EXECUTION_REPORT.md` §7. Ownership comes from
`GOVERNANCE/PRODUCTION_READINESS/PHASE_ZERO_BASELINE.md` (WS-D row and F-04 row).

F-04 verbatim: *"Terminology validation is structural, not release-aware. ICD codes are
pattern-checked, LOINC check digits are not recomputed and UCUM units are an allow-list. No
clinical interpretation, thresholding or CDS is provided. This matches the disclosed synthetic
scope but must not be mistaken for clinical-grade validation."*

Only the three explicitly owned paths were written (§2). All other paths — including `factory.py`,
`main.py`, every route/router, `FINAL_DECISION.md`, all MPI files, every other workstream's source,
tests and reports, and the entire `gula-platform` repository — were read-only.

No production activation was performed: the new package is **not imported by any production
module** (verified by search: all 20 imports of `app.health_core.terminology` are inside the
package itself and its two test files).

---

## 2. Exact changes

| Path | Change |
|---|---|
| `backend/app/health_core/terminology/models.py` | New. `TerminologySystem`, `ValidationStatus` (VALID/INVALID/UNVERIFIED), `VerificationStage`, `CoverageLevel`, `CheckDigitStatus`, frozen `CuratedCode`, `TerminologyRelease` (9 provenance fields + `to_dict()`), frozen `ValidationResult` (release-carrying, `accepted`, `version`, `to_dict()`). |
| `backend/app/health_core/terminology/ports.py` | New. `@runtime_checkable TerminologyValidator` Protocol exposing `system`, `release`, `validate(code)`, `provenance()`. |
| `backend/app/health_core/terminology/errors.py` | New. `TerminologyError` / `UnknownTerminologySystemError` extending the existing `HealthCoreError`. |
| `backend/app/health_core/terminology/curated.py` | New. Curated sets copied verbatim from read-only offline sources: 4 ICD-10, 16 LOINC, 15 UCUM entries; every entry carries a `file:line` `source_ref`. Evidence-based exclusions documented in the module docstring. |
| `backend/app/health_core/terminology/releases.py` | New. Three explicit `TerminologyRelease` records (system, version, canonical URI, source, verification method, licence, verification date, coverage, notes) + immutable `TERMINOLOGY_RELEASES` registry with fail-closed `get_release()` / `all_releases()`. |
| `backend/app/health_core/terminology/validators.py` | New. `IcdValidator`, `LoincValidator`, `UcumValidator` implementing the Protocol: structural stage → curated-allowlist stage; UNVERIFIED for well-formed unknown codes, INVALID for malformed/case-mismatched/identifier-shaped/non-string inputs. No `FULL_RELEASE_CONFORMANCE` and no `CheckDigitStatus.VERIFIED` is ever emitted. |
| `backend/app/health_core/terminology/registry.py` | New. Immutable `VALIDATORS` mapping + fail-closed `get_validator()`, `validator_systems()`, `all_validator_releases()`. |
| `backend/app/health_core/terminology/__init__.py` | New. Public re-exports of the complete interface. |
| `backend/tests/health_core/test_terminology_validators.py` | New. 88 behavioural tests across all adapters, registry, provenance-on-every-result and "never claims full conformance" guarantees. |
| `backend/tests/health_core/test_terminology_provenance.py` | New. 15 AST/source-based tests proving every curated code, version, URI, licence claim and pattern is grounded in the actual offline checkout at HEAD, and that no check-digit function, release dataset or network/DB import exists. |
| This file | WS-D report. |

No router, route, `factory.py`/`main.py`, DDL, migration, schema, dependency, secret or production
activation was introduced. No assertion was deleted, weakened, skipped or xfailed. No code version,
code value or test result was fabricated.

---

## 3. Requirement status

| # | Requirement | Status | Evidence |
|---:|---|---|---|
| 1 | Define a `TerminologyValidator` Protocol with system identity, release version, structured VALID/INVALID/UNVERIFIED result with reason, and provenance access | **VERIFIED** | `ports.py::TerminologyValidator` (`system`, `release`, `validate`, `provenance`); `test_all_adapters_satisfy_the_validator_protocol`; results are frozen `ValidationResult` with `status`, `reason`, `release`, `version`, `accepted`, `to_dict()`. |
| 2 | ICD, LOINC and UCUM adapters with explicit `TerminologyRelease` provenance | **VERIFIED** | Three adapter classes in `validators.py`; three release records in `releases.py` covering all 8 provenance dimensions; `test_provenance_metadata_is_complete_and_consistent`, `test_every_result_carries_consistent_provenance`. |
| 3 | Curated sets sourced ONLY from read-only inspection; unknown codes UNVERIFIED/INVALID, never silently accepted | **VERIFIED** | `curated.py` + `test_every_curated_entry_points_to_a_line_containing_its_code`, `test_ucum_curated_set_equals_offline_ucum_units_allowlist`, `test_loinc_curated_set_includes_every_controlled_fhir_mapping`, `test_icd_codes_are_actually_tagged_as_icd10_in_the_offline_source`; `test_icd_well_formed_unknown_codes_are_unverified`, `test_loinc_unknown_but_well_formed_codes_are_unverified`, `test_ucum_unlisted_but_plausible_units_are_unverified`. |
| 4 | ICD: structural pattern then curated allowlist | **VERIFIED** | `IcdValidator.validate`; `test_structural_patterns_are_documented_including_the_loinc_discrepancy`; ICD pattern matches the offline `ICD_CODE_RE`; malformed-code and curated-accept tests. |
| 5 | LOINC check digit from spec if implementable, else documented | **PARTIALLY VERIFIED / NOT IMPLEMENTED** | No authoritative algorithm or full release dataset exists offline; candidate mod-10/weighted schemes evaluated against the curated codes disagreed, so recomputation was deliberately not implemented. Documented in `LOINC_RELEASE.notes`, `LoincValidator.__doc__`, and every LOINC result (`check_digit = NOT_VERIFIED_OFFLINE`, "check digit NOT recomputed"). Proven by `test_check_digit_verification_is_explicitly_not_implemented` (no check-digit function exists; no result claims `VERIFIED`). See §8. |
| 6 | UCUM: case-sensitive curated unit allowlist | **VERIFIED** | `UcumValidator.validate` uses exact match plus a case-fold diagnostic; `test_ucum_curated_units_are_accepted_exactly`, `test_ucum_case_mismatches_are_invalid`. |
| 7 | Results carry release/provenance | **VERIFIED** | `ValidationResult.release` + `to_dict()["provenance"]`; `test_every_result_carries_consistent_provenance`, `test_release_registry_and_validator_registry_are_lockstep`. |
| 8 | Thorough tests, no skips | **VERIFIED** | 103 focused tests pass (15 provenance + 88 behavioural), 0 skipped / 0 xfailed; full-suite static guard confirms no skip/xfail in the new files. |
| 9 | No placeholders, empty dataclasses, fake success, weakened assertions, fabricated data | **VERIFIED** | Every record has populated fields; all results carry real provenance; `test_no_result_ever_claims_full_release_conformance_or_verified_check_digit`, `test_no_official_release_dataset_is_bundled_in_the_package`. |
| 10 | Full official-release conformance | **BLOCKED (offline)** | No WHO/Regenstrief/UCUM release dataset and no network access. Every release is `PARTIALLY_VERIFIED`; `FULL_RELEASE_CONFORMANCE` / `FULL_RELEASE` are reserved enum members never emitted. See §8. |

---

## 4. Provenance table

| System | Version (as recorded) | Canonical URI | Offline source(s) | Coverage |
|---|---|---|---|---|
| ICD-10 | `UNDECLARED` | `http://hl7.org/fhir/sid/icd-10` | `national/services/cds_engine.py:961,976,991` (ICD10-tagged `I10`/`E11`/`E78`), `health_core/clinical/validation.py:108` (`J18.9` example), URI `integration/standards/terminology.py:31` | `PARTIALLY_VERIFIED` |
| LOINC | `2.81` | `http://loinc.org` | `routes/advanced_integrations.py:64` (declared status version), `fhir/terminology.py:20-32` (11 controlled lab mappings), `health_core/clinical/validation.py:46-52` (5 observation code units), URI `fhir/_reference.py:48` | `PARTIALLY_VERIFIED` |
| UCUM | `UNDECLARED` | `http://unitsofmeasure.org` | `health_core/clinical/validation.py:25-43` (`UCUM_UNITS`, 15 literals), URIs `fhir/_reference.py:62` and `integration/standards/terminology.py:34` | `PARTIALLY_VERIFIED` |

All three records: verified on `2026-11-18`, `verification_method` cites read-only inspection at
HEAD `2827c1ff…`, licence statements cite `GLOSI/SECURITY_AND_LICENSE_POLICY.md:43` and/or
`GLOSI/SOURCE_CATALOG.md:50,52,53`. Asserted by `test_canonical_uris_are_present_in_offline_reference_sources`
and `test_licence_statements_cite_offline_policy_sources`.

**Version honesty notes.** `UNDECLARED` is an auditable fact, not a placeholder version. The `2026`
value at `routes/advanced_integrations.py:65` is an **ICD-11** declared status and belongs to a
different code system — it was deliberately **not** applied to ICD-10. LOINC `2.81` is a declared
runtime status value, **not** an independently verified official release artefact.

**Curated counts:** 4 ICD-10 codes (`J18.9`, `I10`, `E11`, `E78`); 16 LOINC codes (11 FHIR mappings
+ 5 `CODE_UNITS` keys); 15 UCUM units (exact `UCUM_UNITS` literals, case-sensitive). Excluded with
reasoning: local lab fixture units in `lab/catalogue.py` (`10^3/uL`, `mg/L`, `U/L`) and the large
`LOINC:` seed list in `ai/knowledge_graph.py` (knowledge-graph fixture, not a validated release).

**Structural-pattern discrepancy (documented, not silently "fixed"):** the offline
`LOINC_CODE_RE` (`health_core/clinical/validation.py:23`) requires 4-6 leading digits, yet the same
checkout curates 3-digit codes `718-7` and `777-3` (`fhir/terminology.py:23,25`). The adapter uses a
documented 3-6 digit pattern so its own curated set is self-consistent; the discrepancy is recorded
in `LOINC_RELEASE.notes` and asserted in `test_structural_patterns_are_documented_including_the_loinc_discrepancy`.

---

## 5. Test coverage

`test_terminology_validators.py` (88 tests): Protocol conformance, immutable/fail-closed registries,
all 4/16/15 curated entries accepted with the correct release/version/source ref, malformed ICD and
LOINC codes INVALID at the STRUCTURAL stage, well-formed unknown codes UNVERIFIED, UCUM case
mismatches INVALID with a case-sensitivity reason, format negatives (whitespace, control chars,
synthetic refs, identifier-shaped values) INVALID, non-string inputs INVALID for every adapter,
provenance consistency on every result, registry lock-step, curated-set uniqueness and source
refs, and the guarantee that no result claims full release conformance or a verified check digit.

`test_terminology_provenance.py` (15 tests): every curated `file:line` ref actually contains its
code (AST-derived line lookup); UCUM set equals the offline `frozenset`; LOINC set equals the union
of all `LaboratoryCode(...)` literals and all `CODE_UNITS` keys; ICD codes are actually tagged
`"system": "ICD10"`; offline patterns and the LOINC discrepancy are documented; declared versions
are copied, not invented; canonical URIs and licence statements exist in offline sources; check
digit is explicitly not implemented; no release dataset (`*.json/.csv/.xml/.zip`) and no
network/DB import (`httpx`, `requests`, `socket`, `urllib`, `sqlalchemy`, `alembic`) in the package;
all three release records are complete, consistent and `PARTIALLY_VERIFIED`.

No test is skipped, xfailed or weakened.

---

## 6. Exact commands and results

Pinned toolchain: `/tmp/opencode/mpi-venv/bin/python` (Python 3.12.13, pytest 9.1.1, ruff 0.16.10,
mypy 2.4.1). Test environment: `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=.:..`, run from `backend/`.

```bash
# Focused terminology suites (latest, 2026-11-18)
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest \
  tests/health_core/test_terminology*.py -q --tb=short
# 103 passed, 1 warning in 0.59s  (0 failed / 0 skipped / 0 xfailed)
#   test_terminology_provenance.py  15 passed
#   test_terminology_validators.py  88 passed

# Full Health Core suite (latest snapshot, concurrent workstreams active)
... -m pytest tests/health_core -q --tb=short
# 728 collected — 5 failed, 723 passed, 1 warning in 6.35s
# Failures (all in files outside WS-D ownership, untouched by WS-D):
#   test_fhir_roundtrip.py::test_entity_fhir_entity_round_trip_is_field_equal[Observation-...]
#   test_fhir_roundtrip.py::test_entity_fhir_entity_round_trip_is_field_equal[DiagnosticReport-...]
#   test_fhir_roundtrip.py::test_real_service_emitted_entities_round_trip
#   test_fhir_validation.py::test_non_dict_resource_is_rejected
#   test_fhir_validation.py::test_missing_required_field_is_rejected[qualification]
# Root causes are in app/health_core/fhir/* and app/health_core/clinical/*; WS-D never
# modified those files. A repository search proves no production module imports
# app.health_core.terminology, so these failures cannot be caused by WS-D code.

# Ruff — from repository root, only WS-D-owned paths
/tmp/opencode/mpi-venv/bin/python -m ruff check \
  backend/app/health_core/terminology backend/tests/health_core/test_terminology*.py
# All checks passed!

# MyPy — from repository root
MYPYPATH=backend /tmp/opencode/mpi-venv/bin/python -m mypy \
  --config-file pyproject.toml backend/app/health_core/terminology
# Found 2 errors in 1 file (checked 8 source files)
#   backend/app/domain/order_state.py:63,81 — pre-existing baseline no-untyped-def errors
# ZERO errors attributable to WS-D-owned files.
```

The single pytest warning is the pre-existing third-party `StarletteDeprecationWarning`
(`fastapi/testclient.py:1`); no warning originates in WS-D code.

---

## 7. Limitations

1. **Full official-release conformance is BLOCKED offline.** No WHO ICD-10 release file, Regenstrief
   LOINC release file or UCUM release dataset is present, and network access is forbidden. Coverage
   is therefore `PARTIALLY_VERIFIED` against a small curated allowlist. `FULL_RELEASE_CONFORMANCE`
   and `CoverageLevel.FULL_RELEASE` exist only as reserved enum members and are never emitted.
2. **LOINC check digit NOT IMPLEMENTED.** No authoritative algorithm is present in the checkout and
   the full release dataset needed to validate any candidate is absent. Multiple mod-10/weighted
   schemes were evaluated offline against the curated codes and none matched consistently, so no
   recomputation was implemented (rather than guessing an algorithm). Every LOINC result reports
   `CheckDigitStatus.NOT_VERIFIED_OFFLINE`. This is disclosed, not hidden behind a fake success.
3. **Undeclared versions are honest, not placeholders.** ICD-10 and UCUM report `UNDECLARED`;
   LOINC `2.81` is a declared status value, not a verified official release artefact.
4. **No clinical interpretation, thresholding or CDS.** This package answers "is this string in the
   curated offline set?", not "is this clinically correct for this patient.". It is not
   clinical-grade validation and must not be used for care decisions.
5. **Synthetic scope only.** No real code-system database, terminology server, FHIR
   `OperationOutcome` mapping, national profile, production route or data of any kind is wired in.
6. **Full Health Core suite is not green in this snapshot.** Five failures exist in untouched FHIR
   round-trip/validation files (§6); WS-D did not modify, suppress or skip them and does not claim
   the whole suite passes. The task-scoped terminology suites, ruff, and all WS-D-owned files are green.

---

## 8. Handoff requests

1. **Release datasets / authoritative algorithm (program owner).** To move beyond
   `PARTIALLY_VERIFIED`, obtain licence-cleared ICD-10, LOINC and UCUM release artefacts and an
   authoritative LOINC check-digit specification, then fund a separate owner-gated work package.
   Licence review is required (`GLOSI/SECURITY_AND_LICENSE_POLICY.md:43`,
   `GLOSI/SOURCE_CATALOG.md:50,52,53`); none was obtained or redistributed here.
2. **LOINC structural-pattern discrepancy (validation.py owner).** The offline `LOINC_CODE_RE`
   (4-6 digits) rejects curated 3-digit codes `718-7`/`777-3`. Either widen the offline pattern or
   document the exclusion; WS-D left the read-only source unchanged and documented the divergence.
3. **FHIR round-trip / validation failures (WS-B / health_core owner).** Five pre-existing failures
   in `test_fhir_roundtrip.py` and `test_fhir_validation.py` (§6) need their own owner; they are
   unrelated to terminology and outside WS-D's write scope.
4. **No promotion.** This workstream closes F-04 as disclosed synthetic development evidence. It
   does **not** lift the HOLD decision, does not change the MPI REJECT verdict, and does not request
   production activation.

---

## 9. Protection integrity

| Artifact | Observation |
|---|---|
| `gula-integration` HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` — unchanged |
| `FINAL_DECISION.md` | md5 `effdfeaf10234678d83b2668c4489552` — HOLD text intact, untouched |
| MPI audit docs | `MPI_INDEPENDENT_AUDIT_FINDINGS.md` md5 `ea3969d09aaf7b0b28a065838b44a594`, `MPI_FINAL_INDEPENDENT_AUDIT.md` md5 `1a02c01563c93b07a7cdb92c0462bf36` — untouched |
| `gula-platform` | HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, status 0 — untouched |
| Forbidden git actions | None — no commit, push, merge, rebase, PR, `git add`, `git reset` or `git clean` |
| Runtime / production | No DB, DDL, migration, schema, secret, route, deployment or real data; package not imported by any production module |

**Bottom line:** F-04 is closed as far as offline evidence permits: a release-aware validator
Protocol, three adapters, explicit provenance for ICD-10/LOINC/UCUM, and 103 passing tests are in
place. Full-release conformance and LOINC check-digit verification remain explicitly
PARTIALLY VERIFIED / NOT IMPLEMENTED with documented reasons and handoff requests. HOLD and REJECT
are unchanged; promotion is not approved.
