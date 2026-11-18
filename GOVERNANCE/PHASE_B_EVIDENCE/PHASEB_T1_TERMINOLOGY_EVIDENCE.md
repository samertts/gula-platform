# Phase B / M5 / T1 — Terminology Check-Digit Evidence

**Agent:** T1 TERMINOLOGY implementation agent
**Date:** 2026-11-18
**Branch:** `integration/gula-unification-v1`
**HEAD verified at start:** `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (match confirmed; no drift)
**Data class:** synthetic only. No network access, no production activation, no licensed dataset.

## Canonical status assignment

| Item | Status |
|---|---|
| Official Appendix C.1 Mod-10 algorithm (`compute_loinc_check_digit`, `validate_loinc_check_digit`) | IMPLEMENTED |
| Focused T1 regression suite (106 tests) | TESTED |
| Wiring into `LoincValidator.validate()` | INTEGRATED |
| Appendix C.2 letter-prefixed check-digit algorithm | NOT IMPLEMENTED |
| Official licensed LOINC release dataset acquisition | BLOCKED |
| Full-release conformance coverage | BLOCKED (coverage remains `PARTIALLY_VERIFIED`) |
| Independent verification award | **not self-awarded** — not claimed by this agent |
| Production readiness award | **not self-awarded** — not claimed by this agent |

The frozen workstream charter (`GOVERNANCE/NATIONAL_INTEGRATION/03_WORKSTREAM_CHARTERS.md`)
and terminology survey (`09_TERMINOLOGY_SURVEY.md`) still read `NOT IMPLEMENTED` for
LOINC check-digit verification; those documents and `status_registry.json` are
FROZEN during the independent review and were **not** edited. Updating them is a
governance-owner action, not an agent self-award.

## 1. Authoritative source and algorithm boundary

- Source: LOINC Users' Guide, Appendix C.1 "Calculating Mod 10 check digits".
- Canonical URL: `https://loinc.org/check-digit` (last updated 2026-09-30).
- The algorithm was independently fetched and hand-verified **before** this task
  by the program lead; this agent only transcribed it statically. No code fetches
  at import time or runtime and no network library is imported.
- Positions are assigned to the numeric body **right-to-left**; odd positions are
  doubled with the **digits of the product summed**; even positions are added
  directly; `check_digit = (10 - (total % 10)) % 10`.
- Letter-prefixed codes (LP/LL/LA/LG, …) use the different Appendix C.2
  algorithm. That algorithm is **NOT IMPLEMENTED** here. Such inputs are
  detected and reported as `NOT_IMPLEMENTED` by the check-digit API and as
  `INVALID` by the validator. Nothing was invented.

## 2. Hand-verified reference vectors (all reproduced by the implementation)

| Body | Check digit | Full code | Result |
|---|---|---|---|
| `12345` | 5 | `12345-5` | matches (official Appendix C example) |
| `718` | 7 | `718-7` | matches |
| `777` | 3 | `777-3` | matches |
| `4544` | 3 | `4544-3` | matches |
| `2345` | 7 | `2345-7` | matches |

All five vectors are asserted both at `compute_loinc_check_digit` level and at
`validate_loinc_check_digit` level, and are recorded verbatim in
`LOINC_RELEASE.notes`. A separate test proves doubled products are reduced to
digit sums (`5 -> 9`, `7 -> 5`) and that position numbering is right-to-left
(`12 -> 5`, not the left-to-right `6`).

## 3. Integration behaviour

- Curated LOINC code + matching digit → `VALID`, `VERIFIED`, stage
  `CURATED_ALLOWLIST`, source reference and full release provenance retained.
- Curated LOINC code + mismatching digit → `INVALID`, new `MISMATCH`
  check-digit status, no normalized code, no source reference. This path is
  covered with a synthetic curated entry injected into a validator instance;
  `curated.py` was not modified.
- Non-curated but structurally valid code → `UNVERIFIED`, never `VALID`, even
  when its own checksum happens to be correct (e.g. `4544-3`). No checksum
  verdict is disclosed for uncurated codes.
- All 16 curated LOINC codes were recomputed and all 16 match.
- ICD-10 and UCUM behaviour is unchanged (no check digit, no status change).
- Existing `CheckDigitStatus` members were preserved; `MISMATCH` was appended.

## 4. Provenance, lineage and rollback

- `LOINC_RELEASE.notes` now cites Appendix C.1, the canonical URL, the
  2026-09-30 last-updated date, all five vectors, the Appendix C.2 boundary,
  and the honest dataset boundary: licensed acquisition **BLOCKED**, coverage
  `PARTIALLY_VERIFIED`, full-release conformance **NOT claimed**.
- The now-false `check digit NOT recomputed` clause in the LOINC
  `verification_method` was removed for provenance consistency. No other
  release record, version, URI, licence or coverage value was changed; the
  `CHECKOUT_HEAD` marker and `GLOSI/` licence citations remain intact.
- Added a frozen `RELEASE_LINEAGE` tuple plus `resolve_release(version)` and
  `previous_release(system, version)`. They fail closed on empty/unknown
  versions, on the ambiguous `UNDECLARED` version, on unknown systems and when
  no earlier recorded version exists (`NoPreviousReleaseError`). Every record
  carries `official_artifact=False`; version `2.81` is documented as a declared
  runtime status value, **not** an official released artefact.

## 5. Tests executed and exact results

Command prefix (all runs):
`ENV=test PYTHONPATH=.:.. PYTHONDONTWRITEBYTECODE=1 <venv>/bin/python -m pytest ...`

| Scope | Result |
|---|---|
| Baseline before any edit: `pytest tests/health_core -q --tb=short` | **773 passed, 1 warning in 15.23s** |
| Focused: `pytest tests/unit/test_terminology_checkdigit.py -q --tb=short` | **106 passed, 1 warning in 1.18s** |
| Broader: `pytest tests/health_core -q --tb=short` (after implementation) | **21 failed, 752 passed, 1 warning in 8.88s** |
| Broader re-run `--tb=no` (confirm stable) | **21 failed, 752 passed, 1 warning in 7.86s** |
| Ruff on all six owned Python files | **All checks passed!** (0 errors; 1 import-sort issue auto-fixed, 1 ambiguous-fullwidth literal removed) |

### Failure breakdown (21) — no failure is in an agent-owned new file

1. **18 failures are deliberate contract drift in pre-existing, non-owned tests.**
   These tests encode the superseded "check digit NOT implemented" contract and
   assert `check_digit is NOT_VERIFIED_OFFLINE` / "not VERIFIED" /
   "check-digit verification is not implemented" / absence of check-digit
   functions. Fulfilling T1 necessarily contradicts them. They were **not**
   edited because they are outside this agent's disjoint file ownership:
   - `test_terminology_validators.py::test_loinc_curated_codes_are_accepted_with_declared_version` — 16 cases
   - `test_terminology_validators.py::test_no_result_ever_claims_full_release_conformance_or_verified_check_digit` — 1 case
   - `test_terminology_provenance.py::test_check_digit_verification_is_explicitly_not_implemented` — 1 case
2. **3 failures originate in concurrent, non-owned work by another workstream**
   (`app/health_core/fhir_http/*` and `app/health_core/reliability/durable_queue.py`):
   `test_quality_review_static.py` — forbidden runtime dependency roots, stub
   router construction, and stub/fake-success returns. `fhir_http/router.py`
   carries an mtime of 21:27:39, later than this agent's first owned file
   (21:22:21), confirming concurrent creation. No owned file appears in any of
   these violation lists.

Consequently "zero regressions against 773" is **BLOCKED** for this agent:
achieving it would require editing two test files and three other-workstream
source files that are explicitly outside the granted ownership. This is
reported rather than silently patched.

## 6. Remaining BLOCKED / NOT IMPLEMENTED work

- **BLOCKED:** licensed official LOINC release dataset. Full-release conformance
  coverage remains `PARTIALLY_VERIFIED`; no official release artefact is
  claimed.
- **NOT IMPLEMENTED:** Appendix C.2 algorithm for letter-prefixed LOINC codes
  (LP/LL/LA/LG). Deliberately not invented; inputs fail closed.
- **BLOCKED:** stale pre-existing contract tests listed in §5 need their owning
  workstream to update them before `tests/health_core` is green again.
- **Not self-awarded:** INDEPENDENTLY VERIFIED and PRODUCTION READY. This agent
  performed implementation and local testing only.

## 7. Security implications

- `CheckDigitResult.reason` values are fixed module constants. No submitted
  identifier, body, whitespace or control character is interpolated into any
  check-digit diagnostic string (I-2: no identifier leakage in diagnostics).
- The LOINC structural-failure path was changed to a fixed, non-echoing reason;
  the shared ICD/UCUM reason text was left untouched to preserve their behaviour.
- `ValidationResult.code` continues to record the submitted value as the
  explicit subject of a decision (pre-existing contract); `normalized_code` is
  `None` for every rejected LOINC path, and `source_ref` is `None` for
  uncurated and rejected codes.
- Malformed, control-character-bearing, non-string, dash-less, multi-dash and
  prefixed inputs all fail closed; no permissive fallback exists.
- No network import, no licensed content redistribution, no production claim.

## Phase B integration addendum

Path references above to `app/health_core/fhir_http/*` describe concurrent,
untracked work observed during this agent's session. That package was later
relocated to `app/interoperability/fhir_http/` to preserve the WS-E structural
guard; it is not part of this terminology artifact. This addendum is a location
correction only — the terminology evidence and all recorded numbers are unchanged.
