# Sovereign Invariants

These are the **non-negotiable invariants** that every sovereign-phase artifact
must preserve. They extend (and never override) the existing GULA security
invariants in `CLAUDE.md`.

If an implementation cannot satisfy an invariant below, the implementation must
be redesigned. The invariant wins.

---

## I. Tenant Isolation

| ID | Invariant |
|----|-----------|
| TI-1 | Every patient-data query MUST filter by `lab_id = current_user.lab_id`. |
| TI-2 | National-scale queries (epidemiology, MOH reporting) MUST use governed analytical tenants — never raw clinical reads. |
| TI-3 | Federated identity reconciliation MUST NOT leak patient identifiers across tenants without an explicit reconciliation event in the audit chain. |
| TI-4 | Adapter-issued requests carry the **calling institution's** trust-domain context, never the recipient's privileges. |
| TI-5 | Cross-institution joins on `national_id` are forbidden outside reconciliation workflows. |

## II. Audit Integrity

| ID | Invariant |
|----|-----------|
| AI-1 | Audit-log rows are append-only. No mutation, no deletion, no truncation. |
| AI-2 | Hash-chain continuity (audit_logs v2) MUST be preserved across reconciliation, merges, and DR failover. |
| AI-3 | Interoperability calls (inbound + outbound) MUST emit a correlated `InteropAuditEvent`. |
| AI-4 | A failed external integration MUST still produce an audit row (fail-closed audit). |
| AI-5 | Crisis-mode degraded operation MUST queue audit events for chained replay — never drop them. |

## III. Clinical Safety

| ID | Invariant |
|----|-----------|
| CS-1 | Clinical writes (`/results`, `/orders`, `/samples`, `/critical-alerts`) are exempt from concurrency shedding. |
| CS-2 | Optimistic-lock (`version` column) checks on `LabResult` mutations are mandatory; violations fail closed. |
| CS-3 | A merged/reconciled patient record MUST preserve every constituent record's clinical history; merges are logical, not destructive. |
| CS-4 | Critical-result delivery is never silently degraded by interoperability or AI failures. |

## IV. AI Governance

| ID | Invariant |
|----|-----------|
| AG-1 | AI never bypasses clinical authority. A clinician's decision is the source of truth. |
| AG-2 | AI outputs that influence clinical state are logged with explainability metadata (model id, version, feature snapshot). |
| AG-3 | AI fails **closed** in degraded mode — no silent "best-effort" prescriptions, diagnoses, or reimbursements. |
| AG-4 | AI execution remains tenant-scoped; no model has cross-tenant data access without a governed analytics workflow. |
| AG-5 | AI must never silently mutate clinical state. Recommendations are always advisory. |

## V. Privilege Boundaries

| ID | Invariant |
|----|-----------|
| PB-1 | Adapter trust is **bounded** to the operations declared in its trust-domain manifest. |
| PB-2 | An institutional adapter never inherits *user* privileges; it carries **institution** privileges. |
| PB-3 | RBAC extensions for ministry, insurer, regulator, inspector roles are **additive** — they never widen `lab_user` privilege. |
| PB-4 | Regulator/auditor accounts MUST be separated from clinician/administrator accounts at the role level. |
| PB-5 | No role grants the union of "clinical action authority" + "audit modification authority". |

## VI. Operational Survivability

| ID | Invariant |
|----|-----------|
| OS-1 | DR failover preserves audit chain continuity. |
| OS-2 | Regional isolation MUST NOT cause cross-region tenant bleed. |
| OS-3 | Degraded-network operation MUST default to **fail-closed** for writes that affect patient identity, billing, or critical results. |
| OS-4 | Offline edge synchronization MUST be conflict-detectable; conflicts are escalated, never silently merged. |
| OS-5 | Recoveries from partial outages MUST not generate orphaned or duplicate audit rows. |

## VII. Governance & Legal

| ID | Invariant |
|----|-----------|
| GL-1 | Retention policies are configurable but never below regulatory floor. |
| GL-2 | Legal-hold flags suspend any retention-driven purge. |
| GL-3 | Chain-of-custody for sample → result → report is preserved across institutional handoffs. |
| GL-4 | No compliance bypass: every governance escape (e.g., emergency-access override) is itself audited and reviewable. |
| GL-5 | Data sovereignty: patient data persists within the declared national jurisdiction unless a regulator-approved cross-border transfer is recorded. |

---

## Enforcement Hooks

These invariants are partly enforced today (tenant isolation in routes, audit
chain in `audit/`, optimistic locking in result models). The remaining
enforcement work is documented per-phase. Phase 18 is the integration point
that tracks which invariants have:

- **Code-enforced** controls
- **Process-enforced** controls
- **Documentation-only** controls (still pending hard enforcement)

See [`phase18-regulatory-governance/04-audit-integrity.md`](./phase18-regulatory-governance/04-audit-integrity.md)
for the current enforcement state matrix.
