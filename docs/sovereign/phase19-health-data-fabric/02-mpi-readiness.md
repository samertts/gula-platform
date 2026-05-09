# Phase 19-02 — MPI Readiness Framework

The Master Patient Index resolves "who is this patient?" across tenant
boundaries without violating tenant isolation. Today, `services/mpi/` is a
scaffold. Phase 19 codifies the readiness criteria.

## Functional Requirements

| Req | Description |
|-----|-------------|
| MPI-F1 | Given a patient lookup payload, return a confidence-ranked candidate list. |
| MPI-F2 | Never return raw plaintext national_id; return tokens / display fragments. |
| MPI-F3 | Auto-link only on deterministic + secondary-confirmed match. |
| MPI-F4 | Otherwise propose a reconciliation event awaiting human review. |
| MPI-F5 | Maintain immutable reconciliation history. |
| MPI-F6 | Expose only the canonical id to consumers, plus a reverse index for forensic lookup by an authorised operator. |
| MPI-F7 | Run inside the existing tenancy model — an MPI lookup never returns rows from a tenant the caller does not have permission to see, **except** as part of an explicit reconciliation flow. |
| MPI-F8 | Be deterministic given the same input + same source state (re-runs are safe). |

## Non-Functional Requirements

| Req | Description |
|-----|-------------|
| MPI-N1 | Lookup latency P95 ≤ 200 ms for deterministic match. |
| MPI-N2 | Probabilistic match runs asynchronously; no clinical pathway blocks on it. |
| MPI-N3 | All MPI paths fail closed: an MPI error MUST NOT surface a wrong patient. |
| MPI-N4 | MPI is read-mostly; writes are reconciliation events only. |
| MPI-N5 | MPI surface is auditable (every lookup captured in audit chain at the appropriate detail level). |

## Match Algorithm Discipline

For deterministic match (national_id):

1. Apply HMAC; compare against the indexed HMAC.
2. If hit, fetch candidate.
3. Validate secondary attributes (DOB, family-name first 3 chars, locality).
4. If all secondary checks pass with no contradiction: return as
   "deterministic_high".
5. If any secondary check is missing or contradicts: return as
   "deterministic_uncertain" — DO NOT auto-link.

For probabilistic match:

1. Tokenise inputs.
2. Score each candidate by a pre-approved model (rule-based today; ML-based
   only with IRB-AI sign-off).
3. Return ranked list with explicit scores.
4. Always escalate to human review.

## Reviewer UI / Workflow (recommended)

A reviewer:

- sees both records side-by-side with redacted identifiers
- sees the score and the contributing features
- can approve link, reject link, or request more data
- approval is recorded with reviewer id, timestamp, and reason

A two-person rule applies for any merge that crosses province boundaries.

## Audit Chain Format

A reconciliation event row includes:

- `event_id`
- `reviewer_id` (or `automatic` with rule id)
- `match_mode` (`deterministic_high` / `probabilistic`)
- `score`
- `canonical_id_before` / `canonical_id_after`
- `constituent_ids` (lab_id + patient_id pairs)
- `disposition` (`link` / `reject` / `pending`)
- chain hash fields

## Privacy

Reconciliation rows MUST NOT contain plaintext national_id, plaintext
phone, or plaintext family name beyond a short fragment for reviewer
context. Even fragments are redacted in the regulator-export view.

## Failure Modes

| Failure | Behavior |
|---------|----------|
| MPI service down | Lookup returns "no candidate"; clinical workflow proceeds with explicit "no match" — not silent default |
| Deterministic match with conflicting secondary | Mark uncertain; do not link |
| Probabilistic match low confidence | Return empty for auto-link; reviewer queue receives entry |
| Network split between MPI and core | MPI calls fail; clinical workflow proceeds with no-link banner |

## Readiness Criteria for Production

- [ ] Match algorithm signed off by IRB-Interop.
- [ ] Reviewer workflow demonstrated end-to-end on staging.
- [ ] Audit chain integration verified.
- [ ] No code path auto-merges on probabilistic match.
- [ ] Privacy review completed: no plaintext PII in MPI logs or events.
- [ ] Soak test: 30 days on staging with simulated reconciliation load.
