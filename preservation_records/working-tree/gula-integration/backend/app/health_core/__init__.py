"""Health Core — SYNTHETIC DEVELOPMENT ONLY.

This package is an isolated, un-wired development surface for the Health Core
program. It is intentionally NOT imported by ``app.factory`` or ``app.main``:
no route, feature flag, or production path is activated by its presence.

Guarantees enforced across every subpackage:
  * Synthetic fixtures and identifiers only (``SYN-`` prefixed).
  * No real patient data, no national identifiers, no secrets.
  * No MPI / NHID resolution, no canonical-patient writes, no identity links.
  * No database session, no migration, no DDL, no schema change.
  * All patient identity goes through :mod:`app.health_core.identity.port`.

See GOVERNANCE/HEALTH_CORE/HEALTH_CORE_READINESS_ASSESSMENT.md. This code is
development evidence only and MUST NOT be represented as clinically usable or
production ready while FINAL_DECISION.md remains HOLD and MPI remains REJECT.
"""
