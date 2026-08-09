# ADR-037: Next Program Authority (PROGRAM_NEXT_PHASE_PLAN supersedes legacy PROGRAM-02 label)

**Status:** Accepted
**Date:** 2026-08-10
**Deciders:** Program Director (decision recorded per GULA governance protocol)
**Supersedes:** (for future execution planning) the legacy "PROGRAM-02 = Shared Core
Consolidation" label defined in `PROGRAM-01_EXECUTION_FRAMEWORK.md` §10 and
`PROGRAM_01_FINAL_CERTIFICATION.md` §12
**Related:** ADR-028, ADR-029, ADR-030, ADR-031, ADR-032, ADR-033, ADR-034, ADR-035,
ADR-036, PROGRAM-01 certification documents, `docs/programs/PROGRAM_NEXT_PHASE_PLAN.md`

---

## Context

PROGRAM-REPO-01 (repository/release readiness for the national platform) is
certified complete and its architecture is locked (25/25 acknowledged findings,
0 actionable, domain isolation 11/11). Several forward-looking governance
documents refer to the next program by the legacy label "PROGRAM-02 = Shared
Core Consolidation":

- `docs/programs/PROGRAM-01_EXECUTION_FRAMEWORK.md` §10 — "PROGRAM-02
  Readiness" and "PROGRAM-02 scope boundary".
- `docs/programs/PROGRAM_01_FINAL_CERTIFICATION.md` §12 — "PROGRAM-02 Entry
  Criteria" with a Shared Core consolidation scope list.
- `docs/programs/PROGRAM-01_CERTIFICATION_MODEL.md` L3-6 — "PROGRAM-02
  Readiness self-assessment".
- `docs/programs/PROGRAM_01_EXECUTIVE_REVIEW.md` — "PROGRAM-02 charter".

The Program Director has approved `docs/programs/PROGRAM_NEXT_PHASE_PLAN.md`
as the authoritative successor program for GULA. Its scope is the **National
Health Platform Foundation** (Identity, Authorization, Clinical Safety, Data
Governance, Interoperability, National Health Platform foundations), with a
planned implementation wave sequence beginning at Wave A.

The two labels now conflict. This ADR resolves the conflict formally and
conservatively: it records the decision, supersedes the legacy label for
**future execution planning only**, and leaves every certified/historical
record untouched.

## Decision

1. **PROGRAM-REPO-01 is complete.** Its final certification
   (`PROGRAM_01_FINAL_CERTIFICATION.md`) and the frozen Wave 1/2/3/4
   certifications stand; this ADR does not reopen or alter them.
2. **`docs/programs/PROGRAM_NEXT_PHASE_PLAN.md` is the authoritative successor
   program** to PROGRAM-REPO-01, as approved by the Program Director. It is the
   single source of truth for next-program scope, dependency layers, waves, and
   acceptance criteria.
3. **The legacy "PROGRAM-02 = Shared Core Consolidation" label is superseded
   for future execution planning.** Where `PROGRAM-01_EXECUTION_FRAMEWORK.md`
   §10, `PROGRAM_01_FINAL_CERTIFICATION.md` §12, `PROGRAM-01_CERTIFICATION_MODEL.md`
   L3-6, or `PROGRAM_01_EXECUTIVE_REVIEW.md` refer to a "PROGRAM-02" next
   program, that reference is read, going forward, as the successor program
   governed by this ADR — not as a mandate to begin Shared Core consolidation
   as a standalone program. Those documents are historical records and remain
   byte-for-byte immutable.
4. **Existing Shared Core work is an already-established architectural
   foundation** (canonical providers per ADR-029/030/031/032/033/034/035/036,
   `SHARED_CORE_CATALOG`, frozen baseline 25 acknowledged + 2 country). It is
   **not** a reason to reopen PROGRAM-REPO-01 and not a pending standalone
   program; it is consumed as-is by the successor program.
5. **Wave A is the first execution wave of the new program** (identity
   hardening + immutable audit), per the wave table in
   `PROGRAM_NEXT_PHASE_PLAN.md` §5.
6. **Wave A is NOT authorized for execution by this decision.** This ADR is
   governance-only. Any execution requires a separate, explicit Program
   Director authorization per wave, following the commit-isolation and
   one-commit-at-a-time protocol inherited from PROGRAM-REPO-01.
7. **B-8 (frontend-v3 rename) remains deferred.**
8. **v1.0.0 tag / GitHub release remains deferred** (engineering milestones +
   internal certification + RC releases; no `v1.0.0` tag, no release).
9. **National data-flow implementation remains legally gated.** No national
   data sharing without Iraq legal/governance sign-off, per
   `PROGRAM_NEXT_PHASE_PLAN.md` §4.1 and §7.6.
10. **Historical certification documents remain immutable.** No rewrite of any
    certified execution record, wave certification, or historical commit
    description occurs as a result of this ADR.

## Alternatives Considered

### A. Rewrite the "PROGRAM-02" text in the framework / certification documents

Rejected. Those documents are certified historical records; the task expressly
prohibits rewriting historical reports, altering certified execution records,
changing frozen wave certifications, and modifying historical commit
descriptions. A governance ADR supersedes the label without mutating history.

### B. Do nothing (leave the naming conflict unresolved)

Rejected. Two authoritative labels would remain in conflict, allowing a future
executor to begin Shared Core consolidation as a standalone "PROGRAM-02" and
misread `PROGRAM_NEXT_PHASE_PLAN.md` as merely aspirational. The PD decision
must be recorded unambiguously.

### C. Amend `PROGRAM_NEXT_PHASE_PLAN.md` alone

Rejected as insufficient. The plan is the scope/architecture document; it does
not have the authority to supersede the framework's program numbering by
itself. A new ADR is the repository's established mechanism for binding
governance decisions (README §ADR Process; framework §Governance).

## Consequences

**Positive**

- Unambiguous successor program: `PROGRAM_NEXT_PHASE_PLAN.md`, one source of
  truth, approved by the Program Director.
- Legacy "PROGRAM-02 = Shared Core Consolidation" label is superseded for
  future planning without touching any certified record.
- Shared Core consolidation intent is preserved as an established foundation,
  not lost — it is consumed by the successor program.
- Wave A (and every later wave) is explicitly gated on separate PD
  authorization.
- B-8, v1.0.0 tag/release, and national data-flow gates remain deferred and
  legally controlled, as before.

**Negative**

- Documents that still print "PROGRAM-02 = Shared Core Consolidation" (the
  framework §10, final certification §12, certification model L3-6, executive
  review, AGENTS.md anchored summary, PROJECT_BRAIN) are intentionally left
  unchanged; readers must consult this ADR for the effective meaning. This is
  the accepted cost of keeping historical records immutable.

**Neutral**

- No application, backend, frontend, CI, helm, security, database, or release
  change. No tag, no release, no branch/worktree/stash mutation.

## References

- `docs/programs/PROGRAM_NEXT_PHASE_PLAN.md` — authoritative successor program (PD-approved)
- `docs/programs/PROGRAM-01_EXECUTION_FRAMEWORK.md` §10 — legacy "PROGRAM-02 Readiness" (historical)
- `docs/programs/PROGRAM_01_FINAL_CERTIFICATION.md` §12 — legacy "PROGRAM-02 Entry Criteria" (historical)
- `docs/programs/PROGRAM-01_CERTIFICATION_MODEL.md` L3-6 — legacy readiness evidence (historical)
- `docs/adr/README.md` — ADR registry and process
- ADR-028 … ADR-036 — structural migration / canonical provider governance (unchanged)
- `AGENTS.md` — anchored workspace summary (unchanged)
