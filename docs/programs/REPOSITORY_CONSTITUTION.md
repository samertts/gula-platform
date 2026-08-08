# REPOSITORY CONSTITUTION

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2.5-G / F — Repository Constitution (ANALYSIS ONLY — governance DESIGN, no mutations)
**Date:** 2026-08-08
**Status:** DRAFT — the permanent repository governance for GULA Platform. Supersedes ad-hoc
conventions upon Program Director approval.

> **Authority note:** this constitution governs the REPOSITORY (structure, refs, CI, docs). It does
> not alter the application architecture constitution (PROGRAM-CONSTITUTION-001) or the structural
> migration constitution (PROGRAM-MIGRATION-001 / ADR-028). Where this document conflicts with those,
> the higher document wins (AGENTS.md §1.4 precedence).

---

## 1. Directory Ownership

| Directory | Classification | Owner | Guardrails |
|---|---|---|---|
| `backend/` | ACTIVE | Platform Backend | Never moved/renamed; runtime authority |
| `shared/` | SHARED | Platform Kernel | Never moved/renamed; highest fan-out (E-01) |
| `frontend/` (target name for frontend-v3) | ACTIVE | Frontend | Rename only via approved Wave-4 process |
| `mobile/` | ACTIVE | Mobile | Path-stable (3 workflows) |
| `services/` | ACTIVE | Services | Compose build contexts — path-stable |
| `contracts/` | ACTIVE | Integration | SDK publish path-stable |
| `server/` | ACTIVE | Backend Node | Root Dockerfile dependency |
| `governance/` (top-level) | ACTIVE | Governance | Imported by backend (E-16) — verified before any change |
| `security/` | ACTIVE_INFRA | Security | Policies authoritative |
| `config/` | ACTIVE_INFRA | DevOps | Compose/scripts references |
| `terraform/` `k8s/` `helm/` `docker/` `cloudflare/` | ACTIVE_INFRA | DevOps | Image-name refs only |
| `docs/` | ACTIVE_DOC | Docs | Sole doc home (after Wave 1) |
| `scripts/` | TOOLING | Engines | Root of governance engines; path-stable (Makefile) |
| `.ai/` `.github/` `.githooks/` `.agents/` | TOOLING | Governance | Read-only except approved changes |
| `archive/` | ARCHIVED | Governance | Frozen by ADR-028; only additions, never deletions |

**Rule:** every directory has exactly one owner recorded in CODEOWNERS. No directory may exist at
top level without a classification (Phase B) and an owner.

## 2. Naming Conventions

- **Directories:** `kebab-case` (existing exceptions documented; no NEW exceptions).
- **Top-level naming:** one canonical name per product surface. `frontend-v3` is the ONLY active
  frontend; `frontend-v2`, `frontend` are legacy and resolve to `archive/`. Never create `-v2`/`-v3`
  sibling directories — use `archive/` + a single canonical name.
- **Files:** Python `snake_case`; TS/TSX `PascalCase.tsx`/`camelCase.ts`; docs `UPPER_CASE` or
  `kebab-case` per `docs/` area rules; no reserved suffixes (`-v1`, `-v2`, `-copy`, `_FINAL`).
- **Branches:** `feature/<area>-<short>`, `fix/<short>`, `release/vX.Y.Z`, `chore/<short>`.
- **Tags:** `vX.Y.Z` only (SemVer 2.0; optional `-rc.N` pre-release).

## 3. Directory Creation Policy

New top-level directory requires:
1. Classification (Phase B vocabulary) + owner + rationale in a comment/ADR note.
2. Dependency scan showing no name collision and no existing canonical home (REUSE BEFORE BUILD).
3. If documentation → MUST live under `docs/`, never a new root dir.
4. Approval gate: listed in `AGENTS.md` "Relevant Files" + CODEOWNERS entry + `project_brain.py`
   scan roots update (if applicable).

## 4. Directory Retirement Policy

Retire ONLY via ADR-028 (archive-first): `git mv <dir> archive/<name>/` → verify zero importers →
keep forever in `archive/`. Deletion of an archived tree requires 2 consecutive releases without
access + explicit PD approval. Classification lifecycle:
`ACTIVE → DORMANT (2 releases unused) → LEGACY (superseded) → ARCHIVED (moved) → [delete, PD-only]`.

## 5. Documentation Placement Rules

- ALL documentation lives under `docs/` (root holds only README/LICENSE/NOTICE/SECURITY/CONTRIBUTING/
  SUPPORT/GOVERNANCE/CODE_OF_CONDUCT/CITATION/CHANGELOG/AGENTS/CLAUDE/VERSION).
- Program/execution docs → `docs/programs/`; architecture master docs → `docs/architecture/`;
  certifications → `docs/certification/`; reports → `docs/reports/`; NIAM → `docs/niam/`;
  production/DR → `docs/production/`.
- `docs/README.md` is the mandatory index; every new doc must be linked there.
- One canonical home per topic — duplicate basenames across active dirs are prohibited (link the
  canonical doc instead).

## 6. Generator Output Rules

- Every generator writes to a canonical, declared output path (never repo root by default).
- Generator-sourced docs are regenerated, not hand-edited; a comment header declares the generator.
- Generator output path changes MUST be committed together with the generator change (no drift window).
- Zero-drift engines (`zero_drift_engine.py`) gate CI for generated clients.
- Generated scan artifacts (bandit/sbom/semgrep/trivy/grype JSON) are NEVER tracked — CI artifacts only.

## 7. Workflow Placement Rules

- All workflows under `.github/workflows/`; composite actions under `.github/actions/`; shell
  pipeline scripts under `.github/scripts/`.
- Naming: `<area>-<purpose>.yml` (e.g. `security-scan.yml`), matching the target CI set (≤ 12).
- One workflow = one responsibility; deploy strategies are steps/actions, not separate workflows.
- Every workflow declares `paths:` triggers; no workflow may trigger on directories that do not exist
  (delete stale path filters with the tree).

## 8. CI Conventions

- Required gates on `main`: CI (lint+tests), quality-gate (enterprise validation + architecture gate
  + domain cert), security, repo-hygiene.
- `repo-hygiene.yml` enforces: root-file count ≤ 25, active branch count ≤ 5, tag semver, zero broken
  links, no tracked generated JSON, no garbage packs.
- All checks must pass before merge; branch protection blocks force-push; squash-merge default.
- Baseline-protected: ruff 378, tsc 0, eslint 0, architecture gate 25/25 — regressions fail.

## 9. Release Conventions

- SemVer tags `vX.Y.Z`; single source of truth = `VERSION` file (sync root package.json + SDKs via
  release workflow).
- Every tag must have a GitHub Release with CHANGELOG section + assets.
- `release/vX.Y.Z` branches only for stabilization; auto-merge to `main` after release.
- Tag deletion is a governance action (archive-refs before delete).

## 10. Archive Policy

- `archive/` is append-only; entries frozen under ADR-028 with provenance headers.
- Archive via `git mv` (history preserved); each archive commit reversible.
- No new code may be developed inside `archive/`; archive is not scanned by architecture gate.

## 11. Legacy Policy

- A LEGACY tree is superseded but not yet moved; it must be moved to `archive/` within the next
  release cycle, after: (a) all inbound refs re-pointed, (b) CI path filters removed,
  (c) verification of zero importers.
- Legacy trees may NOT receive new features; bugfixes only with PD approval.

## 12. Dormant Policy

- A DORMANT tree is unused but retained (strategic asset — GULA Project Constitution).
- Dormant trees are NOT scanned for lint/typecheck by default; they are excluded from active CI
  triggers and documented in `docs/programs/`.
- Dormant trees may be promoted back to ACTIVE via an ADR; never silently deleted.

## 13. Experimental Policy

- EXPERIMENTAL trees live in `archive/experimental/` (not root) or a clearly-marked subdir, with a
  README stating status, owner, and kill criteria.
- Experimental code is not covered by release gates; it must be archived or promoted within 2 releases.

## 14. Branch Policy

- `main` protected (PR + required checks + no force-push). Long-lived: `main` (+ optional `develop`).
- Feature branches `feature/<area>-<short>`; merge via squash (linear history).
- Auto-delete head branches ON. Stale branches (>60 days, merged) deleted; ambiguous ones archived
  as `refs/archive/branches/*` before deletion.
- Never force-push shared branches; prefer rebase over merge.

## 15. Tag Policy

- Release tags `vX.Y.Z` only; annotated tags. Feature/domain tags are prohibited (migrated away).
- Archive legacy tags as `refs/archive/tags/*` before deletion.
- Tags point to `main` merge commits, never to feature-branch tips.

## 16. Commit Policy

- Conventional Commits: `type(scope): subject` with body explaining WHY.
- Atomic commits (one logical change); no mixed-scope commits.
- Pre-commit `[GULA-AI]` gate enforced; commitlint optional-add (PD decision).
- Every bugfix → regression test; every feature → tests + docs (AGENTS.md Test Policy).
- Working tree always green after each commit (compile, tests, lint, typecheck).

## 17. Repository Evolution Policy

- Structural changes (moves, renames, retirements) require an ADR entry + Migration Impact Report
  (ADR-028) + verification cycle.
- Classification changes (e.g. DORMANT→LEGACY) are recorded in `REPOSITORY_CLASSIFICATION.md` +
  this constitution's appendix.
- Reuse-before-build: search existing trees before creating anything new.

## 18. Future Scalability Policy

- The 4 canonical product homes (`backend/`, `frontend/`, `mobile/`, `shared/`) are load-bearing and
  never renamed.
- New platform surfaces must be added as subdirectories of an existing ACTIVE home or as a new
  classified top-level dir (per §3), never as versioned siblings.
- Monorepo growth is bounded by repo-hygiene gates (root-file count, branch count, pack size);
  exceeding thresholds triggers a consolidation cycle.
- Multi-package extraction (SDK, agents) goes under `contracts/sdk/` and `services/`, never new
  top-level roots without an ADR.

---

*End of Repository Constitution — DRAFT. To be ratified by the Program Director together with the
execution waves.*
