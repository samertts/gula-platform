# Federated Durability and Authority Proposal

Status: `PROPOSAL ONLY / NOT APPROVED`

Date: 2026-11-27

This document records owner-blocked engineering work. It does not authorize a migration, role grant, deployment, transport action, release-gate change, or production-readiness claim. No DDL has been applied.

## 1. Scope

This proposal covers the remaining findings that cannot be closed by source-only changes:

- **F-03:** no durable authority combining institution trust, subject consent, purpose, scope, and canonical audit evidence.
- **A-01:** federation dispatch coordination is process-local.
- **A-02:** audit hash-chain evidence is application-side only.
- **A-03:** outbox retention is bounded while delivery evidence is relied upon for duplicate suppression.
- **N-01:** cross-process duplicate transport is not verified.
- **`federated_envelope.transmit`:** no matching source exists at the isolated base commit; provisioning is proposed only.

## 2. Canonical direction

The owner must designate one durable decision authority. The proposed boundary is:

1. `AuthorizationDecisionService` remains the only authorization decision engine.
2. `CanonicalAuditService` v2 remains the only canonical audit writer/verifier.
3. `outbox_service` remains the only durable dispatch queue.
4. A single owner-designated trust/consent authority binds institution trust, citizen-to-NIAM identity, consent record, purpose, scope, and resource domain before any federated release.
5. `NiamConsentService` remains the consent record authority; the synthetic in-memory federation broker must not be treated as a consent authority.
6. No second MPI, FHIR validator, consent engine, workflow engine, audit chain, or outbox is introduced.

## 3. Proposed durable authority inputs

The authority decision must be derived only from server-held records:

| Input | Proposed canonical source |
|---|---|
| Requesting institution | NIAM organization / federation trust record |
| Target institution | NIAM organization / federation trust record |
| Institution trust relation | owner-designated trust table; active, unrevoked, in-window |
| Citizen-to-NIAM binding | canonical relationship record; unique and verified |
| Consent | `NiamConsent` with matching subject, grantee, purpose, scope, resource domain, and expiry |
| Actor role and membership | NIAM role assignment and active membership |
| Purpose and minimum necessary | approved purpose catalog and resource-domain scope rule |
| Evaluation time | trusted server evaluation time; never a caller-supplied flag |
| Evidence | canonical v2 audit reference plus outbox envelope digest |

Caller-supplied `consent_status`, emergency claims, role assertions, or target scope overrides must not satisfy this authority.

## 4. Proposed invariants and provisioning

The following are proposals for a disposable database and multi-worker test only:

1. Add a unique `dedupe_key` to federated outbox envelopes, derived from an allowlisted, reference-only payload digest. Enforce a database unique constraint before dispatch is marked delivered.
2. Add or designate a durable trust/consent binding table with a uniqueness constraint covering institution pair, citizen binding, purpose, scope, resource domain, and consent version.
3. Keep canonical audit rows append-only at the application boundary and evaluate an owner-approved database trigger or privilege model that prevents `UPDATE`/`DELETE` by the application role.
4. Define retention so outbox delivery evidence is not purged before the canonical audit duplicate-suppression window expires.
5. Require at least two application workers in a disposable PostgreSQL test to observe no duplicate transport side effect for the same envelope digest.
6. Provision `federated_envelope.transmit` only after the owner designates the transport endpoint catalog, reference-only payload schema, retry policy, and monitoring destination. No external endpoint is contacted in this program.

No table, index, constraint, trigger, role grant, seed row, or endpoint is created by this document.

## 5. Free and open-source alternatives considered

Per `docs/constitution/COST_GOVERNANCE.md` and the platform constitution:

| Alternative | Decision |
|---|---|
| PostgreSQL unique constraints, `SELECT ... FOR UPDATE SKIP LOCKED`, and database roles | Preferred. Already self-hosted, open source, and aligned with existing outbox/audit tables. |
| Redis `SETNX` dispatch locks | Not selected as authority. It would add a second coordination store and would not itself provide durable delivery evidence. |
| RabbitMQ/NATS transport semantics | Not selected as the duplicate authority. Broker guarantees do not remove the need for a database uniqueness invariant across business commit and transport side effect. |
| Commercial SIEM / proprietary transaction monitor | Not recommended. Free self-hosted PostgreSQL evidence and existing canonical audit controls are sufficient to evaluate first. |

No paid dependency is proposed.

## 6. Owner decisions required

1. Designate the authoritative institution trust table and organization-to-NIAM mapping.
2. Designate the citizen-to-NIAM binding and consent lookup basis.
3. Approve purpose/scope/resource-domain equivalence rules.
4. Approve the dedupe-key definition and unique constraint.
5. Approve audit append-only privileges or trigger design.
6. Approve outbox retention alignment.
7. Approve transport endpoint catalog and retry policy for `federated_envelope.transmit`.
8. Approve multi-worker PostgreSQL acceptance evidence before any gate review.

Until these decisions exist, synthetic federation remainders stay isolated, fail closed, and outside any release claim.
