# Phase 24-04 — Medico-Legal Governance Analysis

## Reconstructive Power

The platform's audit chain + AI evidence packets + patient-card history
provide reconstructive power. For any clinical event:

- Who ordered.
- Who collected the sample.
- Who performed the test.
- Who released the result.
- Who received the critical alert.
- What AI advice (if any) was provided.
- What human acceptance/rejection occurred.

This is the basis of medico-legal defensibility.

## Liability Boundaries

The platform takes positions on:

- The **clinician** is responsible for clinical decisions.
- The **lab** is responsible for sample/handling/result release.
- The **operator** is responsible for the platform's operational state.
- **AI** is advisory; the human in the loop is responsible.
- **Adapter peers** are responsible for their side per contract.

The platform does NOT take positions on:

- Apportionment among parties (legal counsel + courts).
- Indemnification (legal counsel).
- Insurance coverage of mistakes (insurance contract).

## Evidence Preservation

For an active legal matter:

- a **legal hold** is placed on relevant data (Phase 18).
- retention purges skip held subjects.
- deletion / redaction is suspended.
- all access on held subjects is logged at heightened detail.

Hold lifecycle is itself audited.

## Evidence Disclosure

When a court or regulator orders disclosure:

- the program produces a sealed, signed, time-bounded export
- the export is integrity-verified by the receiver
- the export's transmission is audit-chained

The platform does not respond to ad-hoc disclosure requests; only
properly-authorised process is honoured.

## Cross-Jurisdiction Considerations

For cross-jurisdiction proceedings (e.g., a multinational insurer's audit
across borders), data sovereignty (Phase 24-02) governs whether and how
data leaves jurisdiction. Counsel orchestrates; the platform executes per
policy.

## Forensic Snapshotting

A "moment in time" snapshot for a subject:

- patient + consent state
- canonical id history
- clinical record (orders, results, samples, visits)
- AI invocations + snapshots
- adapter calls referencing the subject
- operator actions
- chain hashes proving integrity

The snapshot is signed; it is the evidentiary unit.

## Clinical-Safety Incident Linkage

Every clinical-safety incident:

- has a record in the clinical-safety committee log
- references the audit subset
- references reconciliation events if any
- references AI evidence packets if any

The committee log is itself preserved per retention policy.

## Limitations

- A reconstruction is only as accurate as the captured audit.
- Where a clinician failed to use the system (paper, verbal, off-system),
  the system can document the absence but not the absent content.
- Generative-AI replay may be approximate; the capability registry notes
  determinism status (Phase 21-04).
