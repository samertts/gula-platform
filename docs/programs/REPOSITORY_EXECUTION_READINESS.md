# REPOSITORY EXECUTION READINESS

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2.5-F / F — Repository Execution Readiness (ANALYSIS ONLY — no mutations)
**Version:** 1.1 (expanded — per-wave full assessment)
**Date:** 2026-08-08
**Status:** DRAFT — readiness assessment. Execution requires Program Director approval.

---

## WAVE 1 — Root Documentation Consolidation

| Item | Assessment |
|---|---|
| **Objectives** | Move ~120 root `.md` → `docs/**`; add docs index; fix broken link; root surface 156→~16 |
| **Prerequisites** | P-1 (generator path re-point: docs.py/report.py ROOT→docs/architecture in same commit); P-2 (AGENTS.md regen); link audit (E-11) |
| **Blocking dependencies** | None (PD approval is the only hard gate) |
| **Risks** | LOW — duplicate regeneration if generators not re-pointed (mitigated: same-commit change) |
| **Rollback complexity** | LOW — single `git revert` per move commit |
| **Validation checklist** | architecture gate 25/25; boot 118; OpenAPI byte-identical; ruff 378; tsc 0; eslint 0; backend full suite PASS; broken-link check 0; `git revert --no-commit HEAD` clean |
| **Estimated duration** | 3–5 hours |
| **Estimated commits** | 3–5 |
| **Estimated PRs** | 1 |
| **Estimated review effort** | 1–2 hrs (structural review only) |
| **Expected repository improvement** | Organization 25→85; Docs Organization 30→85; DX +; OSS Readiness + |

**Wave 1 = SAFE (unconditional).**

---

## WAVE 2 — Legacy Isolation + Git Housekeeping

| Item | Assessment |
|---|---|
| **Objectives** | Archive ~1,100 legacy/dormant files; CI re-point v2→v3; script path updates; git gc + branch cleanup |
| **Prerequisites** | P-3 (E-03 frontend-pwa.yml re-point FIRST); P-4 (E-04 helm image fix); P-5 (E-08 3-script path updates); P-6 (PD sign-off on CI frontend build switch); archive-refs for branches/tags |
| **Blocking dependencies** | B-2 (frontend-pwa builds v2), B-3 (verify `governance/` E-16 runtime resolution) |
| **Risks** | CRITICAL if E-03 skipped (CI break); MEDIUM otherwise — script path errors caught by engine runs |
| **Rollback complexity** | LOW–MEDIUM — 2 reverts (CI + move) per tree; branch deletions recoverable from archive refs |
| **Validation checklist** | all Wave-1 gates + `dependency_guardian`/`repository_scorecard`/`project_brain` green post-path-update + `git fsck --full` clean + `git count-objects` ≤ ~70 MiB + branch count ≤ 5 |
| **Estimated duration** | 6–10 hours |
| **Estimated commits** | 6–9 |
| **Estimated PRs** | 2 (CI-repoint PR; archive PR) |
| **Estimated review effort** | 2–4 hrs |
| **Expected repository improvement** | Maintainability 55→75; Git Hygiene 25→80; CI/CD +; Organization + |

**Wave 2 = SAFE (conditional on E-03/E-04/E-08 first).**

---

## WAVE 3 — Documentation Dedup + CI Consolidation + JSON Removal

| Item | Assessment |
|---|---|
| **Objectives** | Dedup ~25 docs; merge 26→12 workflows; add repo-hygiene gate; remove ~11 MB generated JSON from git |
| **Prerequisites** | P-7 (inbound-link audit E-11 for dedup targets); P-8 (status-check name alignment with branch protection); archive-first per doc |
| **Blocking dependencies** | B-4 (check-name mismatch blocks merges), B-5 (tag cleanup is Wave-4 scope, not here) |
| **Risks** | MEDIUM — workflow merge blast radius (14 files); doc removal with inbound links; check-name drift |
| **Rollback complexity** | MEDIUM — per-workflow revert; doc archive-first; JSON recoverable from history |
| **Validation checklist** | all Wave-1/2 gates + all 12 workflows green + hygiene gate PASS + zero broken links + `git ls-files` shows no `security-audit/*.json` |
| **Estimated duration** | 8–12 hours |
| **Estimated commits** | 8–12 |
| **Estimated PRs** | 2–3 |
| **Estimated review effort** | 3–5 hrs (CI change requires careful review) |
| **Expected repository improvement** | CI/CD 45→80; Maintainability +; Security + (artifact hygiene); Organization + |

**Wave 3 = SAFE (conditional on B-4).**

---

## WAVE 4 — OSS Governance + Release Stream (+ Optional Rename)

| Item | Assessment |
|---|---|
| **Objectives** | SECURITY/CONTRIBUTING/SUPPORT refresh; CODEOWNERS expansion; branch protection; VERSION-sync; semver tags; OPTIONAL frontend-v3→frontend rename |
| **Prerequisites** | P-9 (PD approval for tag cleanup — public refs); P-10 (version single-source decision); P-11 (for rename: E-09/E-04/E-05 re-point + zero-drift green) |
| **Blocking dependencies** | B-6 (tag public-ref change needs PD), B-7 (version drift decision needs PD), B-8 (rename optional PD decision) |
| **Risks** | MEDIUM — tag deletion (public), version-sync race, rename import surface (highest) |
| **Rollback complexity** | MEDIUM — revert commits; re-tag from archive refs; rename revertible |
| **Validation checklist** | all prior gates + VERSION == package.json == latest tag + GitHub Release created + branch protection active + zero-drift PASS + semver tag stream |
| **Estimated duration** | 8–14 hours |
| **Estimated commits** | 6–10 |
| **Estimated PRs** | 2–3 |
| **Estimated review effort** | 2–4 hrs |
| **Expected repository improvement** | Release 30→85; GitHub Governance 55→85; OSS Readiness 50→85; DX + |

**Wave 4 = SAFE (conditional on PD decisions; rename strictly last/optional).**

---

## OVERALL READINESS

| Wave | Executable | Gate |
|---|---|---|
| Wave 1 | **YES (95%)** | PD approval only |
| Wave 2 | **YES (75%)** | B-2, B-3 |
| Wave 3 | **YES (70%)** | B-4 |
| Wave 4 | **YES (65%)** | B-5, B-6, B-7, B-8 |

**Number of SAFE waves:** 4 (1 unconditional, 3 conditional with documented pre-conditions)
**Number of UNSAFE waves:** 0 (none is unsafe once blockers are resolved; Wave 2 is CRITICAL only if
E-03 is skipped — the plan mandates it first)

**Recommended execution order:** Wave 1 → Wave 2 → Wave 3 → Wave 4 (with mandatory STOP + report +
approval after each wave, per AGENTS.md / ADR-028).

**Repository execution readiness: ≈ 75%** (weighted across waves, blockers resolvable).
