# GLOSI Phase 2 — Registry and Validation Layer

**Date:** 2026-11-15
**Status:** PASS
**Scope:** Registry schema, deterministic builder, validator/exporter, and quality tests.

## 1. Delivered artifacts

| Artifact | Description |
|---|---|
| `GLOSI/MASTER_REGISTRY_SCHEMA.md` | Registry v1.0.0 schema and validation contract |
| `GLOSI/tools/build_initial_registry.py` | Deterministic stdlib builder for the initial 16 records |
| `GLOSI/tools/glosi_registry.py` | Stdlib validator, canonical exporter, summary, and history-preserving update API |
| `GLOSI/REGISTRY/registry.json` | Canonical machine-readable registry (16 records) |
| `GLOSI/DECISION_RECORDS/GLOSI-DEC-0001-*.md` | One proposed decision record per project |
| `GLOSI/tests/test_registry.py` | 20 quality-gate tests |

## 2. Validation commands and results

| Command | Result | Exit code |
|---|---|---|
| `python3 GLOSI/tools/build_initial_registry.py` | Wrote 16 records | 0 |
| `python3 GLOSI/tools/glosi_registry.py validate GLOSI/REGISTRY/registry.json` | `PASS ... records=16` | 0 |
| `python3 GLOSI/tests/test_registry.py` | 20 tests passed | 0 |

## 3. Enforced rules

- Unique `GLOSI-NNNN` and `GLOSI-DEC-NNNN` identifiers.
- Required identity, technical, legal, security, operational, GULA, evaluation, decision, and history sections.
- HTTPS official and evidence URLs; ISO dates.
- Exact 100-point weights and bands; weighted totals are recomputed.
- `COMPLETE` requires all nine numeric scores, evidence per score, and a matching band.
- `PARTIAL` and `NOT_EVALUATED` cannot carry a weighted total or band.
- `APPROVED` requires COMPLETE evaluation, known license, legal review, security review, named reviewers, and an ADR.
- `ADOPT`/`INTEGRATE`/`ADAPT` block unknown or incompatible licenses and critical security findings.
- Canonical export is stable; updates append to `evaluation_history` and never delete prior entries.

## 4. Current registry state

- 16 records, `GLOSI-0001` through `GLOSI-0016`.
- Every evaluation is `PARTIAL` with `LOW` confidence and null dimension scores.
- Every decision is `PROPOSED`; none is `APPROVED`.
- No project has been imported, integrated, or adopted by GULA.

## 5. Phase result

**PASS** — The registry is structurally valid and its quality gates execute successfully.

**Limitation:** Structural validity is not substantive evaluation. All records remain evidence-incomplete and unapproved.
