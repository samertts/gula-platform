# Phase 23-03 — Emergency Governance Procedures

## Authorities Invoked in Crisis

- IC (incident commander)
- Operations chief
- Clinical-safety committee chair
- Security officer
- Regulator liaison

## Emergency Decision Powers

In CRISIS mode (declared by ops chief):

- Mode transitions (RED → CRISIS → PAPER) require ops chief sign.
- Edge isolation declarations (cut a province from central) require ops
  chief sign.
- Manual identity assignments (new local id during crisis) follow the
  pre-printed-id supply protocol.
- Emergency access escalations: see below.

Even in CRISIS, the platform's invariants remain in force:

- No silent audit deletion (AI-1).
- No unauthorized clinical override (CS-2).
- No ungoverned AI execution (AG-3).

## Emergency Access (Break-Glass)

A break-glass account allows emergency clinical operation when normal
access paths are compromised (e.g., the SSO IdP is offline).

Contract:

- Pre-issued, secret-stored credentials kept in a sealed envelope at the
  facility.
- Use produces a `break_glass.invoked` audit row, signed.
- Use is valid for a TTL (e.g., 8 hours).
- Use triggers immediate notification to the security officer + IC.
- Post-event review within N business days.

Break-glass MUST NOT be used as a routine bypass. Misuse is a SEV-2.

## Crisis Reconciliation Governance

Reconciliation events created during crisis:

- carry the crisis_marker
- are processed under Phase 19 reconciliation governance
- get heightened scrutiny
- are reviewed in the post-crisis review

## Patient Communication in Crisis

- Clinical-critical communications continue via available channels.
- Non-critical financial/admin communications may be deferred.
- Communications are logged; the absence of communication during a known
  outage is itself documented.

## Regulator Notification

For SEV-1 crisis:

- Pre-notification within the contractual SLA.
- Periodic updates (typically every 4 hours during active crisis).
- Final after-action report within 14 days.

## After-Action Review

Structure (mandatory for any CRISIS-mode entry):

1. Timeline (audit-chain-derived).
2. Decisions taken, by whom.
3. What worked.
4. What failed.
5. Doctrinal updates.
6. Risk-register updates.
7. Sign-off by ops chief + clinical-safety chair + security officer.

The review feeds Phase 17 dependency register and the deployment
checklist.

## Limitations

- Emergency governance does not bestow new powers; it activates pre-agreed
  authorities under known conditions.
- "Field improvisation" is documented and reviewed; it is never silently
  normalised.
