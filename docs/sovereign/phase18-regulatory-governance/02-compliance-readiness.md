# Phase 18-02 — Compliance Readiness

## Compliance Traceability Mapping

For each in-scope standard (see `STANDARDS_MAPPING_MATRIX.md`), the
compliance readiness package must contain:

1. **Scope statement** — clauses in scope, clauses out of scope, with
   reasoning.
2. **Evidence map** — code paths, configuration, runbooks, audit policies
   that constitute evidence.
3. **Gap register** — concrete missing controls.
4. **Remediation plan** — owner, ETA, dependent phase.

### Evidence Map (illustrative — ISO 15189)

| Clause area | Evidence |
|-------------|----------|
| 4.1 Organisation & management | Governance architecture; role-separation matrix; sign-off framework |
| 4.13 Control of records | Audit chain (immutable, hash-linked); retention policy |
| 4.14 Internal audits | Quarterly governance checklist; tabletop exercises |
| 5.5 Examination procedures | Lab-order state machine; result release governance |
| 5.8 Reporting of results | Critical-result delivery SLAs; chain-of-custody from sample to result |
| 5.10 Lab information management | Tenant isolation; backup; DR readiness; access controls |

## Retention Policy Enforcement Hooks

Until the recommended `retention_policy` table exists, retention is
enforced by:

- Code-enforced: clinical-result rows are never deleted (no DELETE path).
- Code-enforced: audit-log rows are append-only.
- Process-enforced: backups retained for the regulatory window; cold archive
  encrypted.

Recommended evolution:

```
retention_policy
+-----------+--------------+-----------------+-------------+
| data_class| min_years    | jurisdiction    | reviewer    |
+-----------+--------------+-----------------+-------------+
| audit     | 30           | IQ-MOH          | regulator   |
| result    | 30           | IQ-MOH          | regulator   |
| order     | 15           | IQ-MOH          | regulator   |
| identity  | per-life+10  | IQ-MOH          | regulator   |
| billing   | 10           | IQ-MOF          | regulator   |
| logs      | 2            | program owner   | program     |
+-----------+--------------+-----------------+-------------+
```

The numbers are illustrative; the **table shape** is the policy contract.

## Legal-Hold Mechanics

Legal holds suspend retention for a subject. The mechanism, when implemented:

1. A hold is created with: subject (patient | tenant | sample | order),
   scope (data classes), reason (free text), creator, reviewer, expiry, or
   "until cleared".
2. Retention purge processes consult holds **first**; a held subject is
   skipped with an audit record.
3. Holds are themselves auditable; lifting a hold is auditable.
4. A hold cannot be deleted; it can be **cleared** (a state change), which
   is itself audited.

Until coded, holds are administered out of band; the platform must not
auto-purge any data that could be subject to hold.

## Compliance Reporting

Regulators and auditors are served via:

- Read-only `INTEROP_REGULATOR_READ` adapter (Phase 16).
- Direct read accounts with `REGULATOR_READ_FULL` role (Phase 18).
- Periodic compliance report exports — anonymized where possible — generated
  via reporting jobs (deferred to a coding phase).

A regulator's session itself is fully audited; their query patterns are
reviewable.

## Self-Assessment

Annually, the program runs a self-assessment:

- Each in-scope standard's gap register is refreshed.
- Each gap is reviewed for remediation progress.
- Documented-only controls are challenged: can any be promoted to
  process-enforced or code-enforced?

The self-assessment is filed with the regulator liaison and feeds the
deployment checklist.

## Definition of "Compliance-Ready"

The platform is **compliance-ready** for a given standard when:

- Scope is documented.
- Evidence map is current and verifiable.
- Gap register has no severity-1 open items.
- Remediation plan is on schedule.
- Annual self-assessment has been signed in the last 12 months.

Compliance-ready is not the same as certified. Certification requires an
external auditor and is out of scope for this documentation.
