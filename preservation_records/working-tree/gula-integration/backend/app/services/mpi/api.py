"""MPI HTTP API — resolve / lookup / merge.

Endpoints:
    POST /mpi/resolve          — find or create the canonical citizen for a lab patient
    GET  /mpi/citizens/{ulid}  — admin-only projection (no raw PII)
    POST /mpi/merge            — admin-only manual merge

All endpoints require authentication. Resolve enforces lab ownership:
a user can only resolve patients in their own lab (ABAC via require_own_lab).
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ... import database as _database
from ...database import get_db
from ...models.audit_log import AuditLog
from ...models.lab_user import LabUser
from ...models.patient import Patient
from ...security.consent_dep import require_consent
from ...security.dependencies import get_current_user
from ...security.rate_limit import rate_limit_user
from ...security.rbac import require_own_lab, require_role
from . import resolver as mpi_resolver
from .models import Citizen, IdentityClaim, MergeAudit
from .reliability import bounded_retry
from .schemas import (
    CitizenResponse,
    MergeRequest,
    MergeResponse,
    PendingReviewItem,
    PendingReviewPage,
    ReconciliationItem,
    ReconciliationPage,
    ResolveDecision,
    ResolveRequest,
    ResolveResponse,
)

router = APIRouter(prefix="/mpi", tags=["mpi"])


# ── Transaction-lifecycle helpers (MPI-04/05/07) ─────────────────────────────
# The API layer owns the outer transaction. A transaction-scoped advisory lock
# and the merge SAVEPOINT live below it; SAVEPOINT RELEASE is NOT a commit.
# Every response is materialised from captured column values BEFORE commit
# because `expire_on_commit=True` would otherwise turn response building into
# post-commit SELECTs (and a lost connection after commit could look like a
# failure and trigger a duplicate write).


def _resolve_response(outcome: mpi_resolver.ResolveOutcome) -> ResolveResponse:
    return ResolveResponse(
        citizen_ulid=outcome.citizen.citizen_ulid,
        match_method=outcome.match_method,
        match_score=outcome.match_score,
        created=outcome.created,
        features=outcome.features,
    )


def _merge_response(audit: MergeAudit, *, primary_ulid: str, secondary_ulid: str) -> MergeResponse:
    return MergeResponse(
        event_id=audit.id,
        primary_ulid=primary_ulid,
        secondary_ulid=secondary_ulid,
        occurred_at=audit.occurred_at,
        entry_hash=audit.entry_hash,
    )


def _resolve_reconcile(*, lab_id: int, local_patient_id: int) -> ResolveResponse | None:
    """Resolve an in-doubt `resolve` commit by idempotency lookup.

    Uses a fresh session on a fresh connection. Returns the already-persisted
    outcome when the first attempt actually committed, otherwise ``None`` so
    the bounded retry may replay exactly once.
    """
    session = _database.SessionLocal()
    try:
        claim = (
            session.query(IdentityClaim)
            .filter_by(lab_id=lab_id, local_patient_id=local_patient_id)
            .first()
        )
        if claim is None:
            return None
        citizen = session.query(Citizen).filter(Citizen.id == claim.citizen_id).first()
        survivor = citizen.canonical() if citizen else None
        effective = survivor or citizen
        return ResolveResponse(
            citizen_ulid=effective.citizen_ulid if effective else "",
            match_method=claim.match_method,
            match_score=float(claim.match_score) if claim.match_score is not None else None,
            created=False,
            features=claim.match_features or {},
        )
    finally:
        session.close()


def _decision_reconcile(
    *, claim_id: int, canonical_decision: str
) -> dict[str, object] | None:
    """Reconcile an in-doubt review-decision commit on a FRESH session (AUD-01/05).

    The claim is re-pointed (never deleted) and its ``match_method`` leaves the
    'pending_review' state on the first successful decision, so it is a stable
    idempotency sentinel: if a transient error masked a committed decision we
    return its recorded result instead of minting a second citizen.
    """
    session = _database.SessionLocal()
    try:
        claim = session.query(IdentityClaim).filter(IdentityClaim.id == claim_id).first()
        if claim is None or claim.match_method == "pending_review":
            return None
        citizen = session.query(Citizen).filter(Citizen.id == claim.citizen_id).first()
        features = claim.match_features or {}
        confirmed = canonical_decision == "ACCEPT_MATCH"
        return {
            "claim_id": claim_id,
            "status": "confirmed" if confirmed else "rejected",
            "decision": canonical_decision,
            "previous_citizen_id": features.get("rejected_citizen_id"),
            "new_citizen_ulid": citizen.citizen_ulid if citizen else None,
            "match_method": claim.match_method,
        }
    finally:
        session.close()


def _find_merge_replay(
    db: Session, *, primary_ulid: str, secondary_ulid: str, reason: str
) -> MergeResponse | None:
    """Return the original result for an already-applied merge, unordered pair.

    Normalises primary/secondary replay (a client that reconnects may swap the
    two ULIDs) by matching the *unordered* citizen-id pair on the audit ledger.
    A replay carrying a different reason is a conflict and is rejected rather
    than silently accepted. No new mutation is written on this path.
    """
    a = db.query(Citizen).filter(Citizen.citizen_ulid == primary_ulid).first()
    b = db.query(Citizen).filter(Citizen.citizen_ulid == secondary_ulid).first()
    if a is None or b is None:
        return None
    row = (
        db.query(MergeAudit)
        .filter(MergeAudit.event_type == "manual_merge")
        .filter(
            or_(
                and_(
                    MergeAudit.primary_citizen_id == a.id,
                    MergeAudit.secondary_citizen_id == b.id,
                ),
                and_(
                    MergeAudit.primary_citizen_id == b.id,
                    MergeAudit.secondary_citizen_id == a.id,
                ),
            ),
        )
        .order_by(MergeAudit.id.desc())
        .first()
    )
    if row is None:
        return None
    if (row.decision_reason or "") != reason[:500]:
        raise HTTPException(status_code=409, detail="conflicting merge replay")
    primary = db.query(Citizen).filter(Citizen.id == row.primary_citizen_id).first()
    secondary = db.query(Citizen).filter(Citizen.id == row.secondary_citizen_id).first()
    return MergeResponse(
        event_id=row.id,
        primary_ulid=primary.citizen_ulid if primary else primary_ulid,
        secondary_ulid=secondary.citizen_ulid if secondary else secondary_ulid,
        occurred_at=row.occurred_at,
        entry_hash=row.entry_hash,
    )


# ── POST /mpi/resolve ────────────────────────────────────────────────────────


@router.post("/resolve", response_model=ResolveResponse, status_code=200)
def resolve(
    data: ResolveRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResolveResponse:
    """Find or create the canonical citizen for a LIMS patient.

    Idempotent: re-calling for the same (lab_id, patient_id) returns the
    existing claim.
    """
    rate_limit_user(request, current_user.id, max_per_minute=60)
    # ABAC: must be a user in the target lab (platform admins may cross labs)
    require_own_lab(current_user, data.lab_id)

    # Sanity check: the LIMS patient exists and belongs to the declared lab
    patient = (
        db.query(Patient)
        .filter(Patient.id == data.patient_id, Patient.lab_id == data.lab_id)
        .first()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="patient not found in this lab")

    # AUD-03: the request-scoped `db` has an open read transaction and a pinned
    # pooled connection.  Release it now -- before bounded_retry opens its own
    # fresh session -- so a single request never holds two connections while
    # waiting on the global advisory lock.  All values needed below are scalars
    # captured above.  (get_db's finally close() is idempotent.)
    db.close()

    # Split birth_date into parts (matcher uses them independently)
    by = bm = bd = None
    if data.birth_date is not None:
        by = data.birth_date.year
        bm = data.birth_date.month
        bd = data.birth_date.day

    def _operation(session: Session) -> ResolveResponse:
        # Materialise the response BEFORE commit: expire_on_commit=True would
        # otherwise force post-commit lazy SELECTs on a possibly-dead session.
        return _resolve_response(
            mpi_resolver.resolve_identity(
                session,
                lab_id=data.lab_id,
                local_patient_id=data.patient_id,
                name=data.name,
                phone=data.phone,
                birth_year=by,
                birth_month=bm,
                birth_day=bd,
                gender=data.gender,
                national_id=data.national_id,
                family_id=data.family_id,
                claimed_by_user_id=current_user.id,
            )
        )

    def _reconcile() -> ResolveResponse | None:
        return _resolve_reconcile(
            lab_id=data.lab_id, local_patient_id=data.patient_id
        )

    try:
        # One bounded transaction owned by bounded_retry (first attempt + at
        # most two fresh-session retries, 25/50 ms backoff). Failed sessions
        # are never reused; an in-doubt commit is reconciled by the claim key.
        return bounded_retry(
            _database.SessionLocal,
            _operation,
            reconcile=_reconcile,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail="MPI resolve could not be committed"
        ) from exc


# ── GET /mpi/citizens/{ulid} ─────────────────────────────────────────────────


@router.get("/citizens/{citizen_ulid}", response_model=CitizenResponse)
def get_citizen(
    citizen_ulid: str,
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
            "province_admin",
        ),
    ),
    db: Session = Depends(get_db),
) -> CitizenResponse:
    """Admin-only projection of a canonical citizen.

    Never exposes raw PII (name, phone, NID). The citizen's own portal
    uses a different endpoint after consent verification.
    """
    citizen = db.query(Citizen).filter(Citizen.citizen_ulid == citizen_ulid).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    merged_into_ulid = None
    if citizen.merged_into_id is not None:
        survivor = citizen.canonical()
        if survivor is not None and survivor.id != citizen.id:
            merged_into_ulid = survivor.citizen_ulid

    return CitizenResponse(
        citizen_ulid=citizen.citizen_ulid,
        nid_verified=citizen.nid_verified,
        birth_year=citizen.birth_year,
        gender=citizen.gender,
        status=citizen.status,
        merged_into_ulid=merged_into_ulid,
        created_at=citizen.created_at,
    )


# ── POST /mpi/merge ──────────────────────────────────────────────────────────


@router.post("/merge", response_model=MergeResponse, status_code=200)
def manual_merge(
    data: MergeRequest,
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
        ),
    ),
    db: Session = Depends(get_db),
) -> MergeResponse:
    """Manually merge two citizens (master/ministry admin only).

    Appends a hash-chained mpi_merge_audit entry; secondary transitions to
    status='merged' with merged_into_id pointing at the primary.
    """
    replay_kwargs = {
        "primary_ulid": data.primary_ulid,
        "secondary_ulid": data.secondary_ulid,
        "reason": data.reason,
    }

    # Idempotent replay (including reversed primary/secondary order): return the
    # original audited result without any new mutation. A conflicting reason is
    # rejected by `_find_merge_replay` with HTTP 409.
    replay = _find_merge_replay(db, **replay_kwargs)
    if replay is not None:
        return replay

    def _operation(session: Session) -> MergeResponse:
        # Audit and citizen state are written by the resolver inside ONE outer
        # transaction; the SAVEPOINT it opens is rolled back on verification
        # failure but its RELEASE is not a commit. Response is captured here,
        # before the commit that bounded_retry owns.
        audit = mpi_resolver.merge_citizens(
            session,
            **replay_kwargs,
            decided_by_user_id=current_user.id,
        )
        return _merge_response(
            audit,
            primary_ulid=data.primary_ulid,
            secondary_ulid=data.secondary_ulid,
        )

    # AUD-05: reconciliation MUST use its own fresh session/connection.  The
    # request `db` opened a transaction in _find_merge_replay above; reading an
    # ambiguous-commit result through it can hide a just-committed merge under
    # a raised isolation level or an idle-in-transaction kill.  Mirror
    # `_resolve_reconcile` and `_decision_reconcile` exactly.
    def _reconcile() -> MergeResponse | None:
        session = _database.SessionLocal()
        try:
            return _find_merge_replay(session, **replay_kwargs)
        finally:
            session.close()

    # AUD-03: release the request connection before bounded_retry opens its own.
    db.close()

    try:
        return bounded_retry(
            _database.SessionLocal,
            _operation,
            reconcile=_reconcile,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid request") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail="MPI merge could not be committed"
        ) from exc


# ── GET /mpi/review — list ambiguous claims (0.70-0.90 score) ────────────────


@router.get("/review", response_model=PendingReviewPage)
def list_pending_review(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
            "province_admin",
        ),
    ),
    db: Session = Depends(get_db),
) -> PendingReviewPage:
    """Admin queue of identity claims awaiting adjudication.

    These are matches where the probabilistic score landed in the fuzzy band
    (THRESHOLD_REVIEW ≤ score < THRESHOLD_AUTO). Leaving them unreviewed
    either loses cross-lab linkage (false negative) or conflates two real
    people (false positive, catastrophic at national scale).
    """
    base = db.query(IdentityClaim).filter(IdentityClaim.match_method == "pending_review")
    total = base.count()
    rows = base.order_by(IdentityClaim.created_at.asc()).offset(offset).limit(limit).all()

    items: list[PendingReviewItem] = []
    for claim in rows:
        citizen = db.query(Citizen).filter(Citizen.id == claim.citizen_id).first()
        items.append(
            PendingReviewItem(
                claim_id=claim.id,
                citizen_ulid=citizen.citizen_ulid if citizen else "",
                lab_id=claim.lab_id,
                local_patient_id=claim.local_patient_id,
                match_score=float(claim.match_score) if claim.match_score is not None else None,
                match_features=claim.match_features or {},
                created_at=claim.created_at,
            ),
        )
    return PendingReviewPage(total=total, items=items)


# ── GET /mpi/reconciliation/outstanding — monitored temporary identities ────


@router.get("/reconciliation/outstanding", response_model=ReconciliationPage)
def list_outstanding_reconciliations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
            "province_admin",
        ),
    ),
    db: Session = Depends(get_db),
) -> ReconciliationPage:
    """Admin monitor for MPI identities still needing reconciliation.

    P-16 / AUD-F16 condition F1. The claim-based ``/mpi/review`` queue cannot
    see patients created during an MPI outage: no claim was written in that
    case. This endpoint reads the canonical audit markers
    (``mpi_resolve_failed`` / ``mpi_pending_review``) so degraded and temporary
    identities become observable and can be worked by operations.

    Rows are grouped by ``reconciliation_key`` so repeated retries cannot
    inflate the count. Only identifiers and status are returned — never raw
    national IDs, names, phone numbers or exception text.
    """
    rows = (
        db.query(AuditLog)
        .filter(
            AuditLog.action.in_(["mpi_pending_review", "mpi_resolve_failed"]),
            AuditLog.resource_type == "patient",
        )
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        .all()
    )
    grouped: dict[str, ReconciliationItem] = {}
    for row in rows:
        details: dict[str, object] = {}
        if row.details:
            try:
                parsed = json.loads(row.details)
                if isinstance(parsed, dict):
                    details = parsed
            except (ValueError, TypeError):
                details = {}
        key = str(details.get("reconciliation_key") or f"patient:{row.resource_id}")
        existing = grouped.get(key)
        if existing is not None:
            existing.marker_count += 1
            continue
        grouped[key] = ReconciliationItem(
            reconciliation_key=key,
            patient_id=row.resource_id,
            lab_id=row.lab_id,
            status=str(details.get("status") or "degraded"),
            source=str(details["source"]) if details.get("source") is not None else None,
            error_type=str(details["error_type"]) if details.get("error_type") is not None else None,
            citizen_ulid=(
                str(details["citizen_ulid"]) if details.get("citizen_ulid") is not None else None
            ),
            first_seen_at=row.created_at,
        )
    ordered = sorted(grouped.values(), key=lambda item: item.first_seen_at)
    return ReconciliationPage(total=len(ordered), items=ordered[offset : offset + limit])


# ── POST /mpi/review/{claim_id}/decide — adjudicate a pending claim ──────────


@router.post("/review/{claim_id}/decide", status_code=200)
def decide_pending_review(
    claim_id: int,
    decision: ResolveDecision,
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
            "province_admin",
        ),
    ),
    db: Session = Depends(get_db),
):
    """Adjudicate an ambiguous claim with one of four explicit decisions.

    AUD-01 fix: a REJECT_MATCH / CREATE_NEW_IDENTITY decision mints a brand-new
    canonical citizen through ``create_detached_citizen`` and NEVER re-scores
    the patient.  The rejected citizen (and any other high-scoring candidate)
    can therefore never be silently re-linked.  Every applied decision writes
    one hash-chained audit row with the reviewer, reason, rejected candidate
    and decision time (AUD-11).  The whole decision is atomic and replay-safe.

    Response ``status`` keeps the legacy 'confirmed'/'rejected' values for
    backward compatibility; a new 'decision' field carries the canonical value.
    """
    canonical_decision = mpi_resolver.normalize_review_decision(decision.decision)
    reason = decision.reason

    # Read-only pre-check on the request session, then RELEASE it before the
    # bounded retry so the retry/fresh-session reconcile never needs a second
    # pooled connection while this one holds an open read transaction (AUD-03).
    claim = db.query(IdentityClaim).filter(IdentityClaim.id == claim_id).first()
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")
    if claim.match_method != "pending_review":
        raise HTTPException(
            status_code=409, detail=f"claim is not pending (method={claim.match_method})",
        )

    old_citizen_id = claim.citizen_id
    lab_id = claim.lab_id
    local_patient_id = claim.local_patient_id
    db.close()

    # NEEDS_MANUAL_REVIEW is an explicit no-op: the claim remains in the queue.
    if canonical_decision == "NEEDS_MANUAL_REVIEW":
        return {
            "claim_id": claim_id,
            "status": "needs_manual_review",
            "decision": canonical_decision,
            "previous_citizen_id": old_citizen_id,
            "new_citizen_ulid": None,
            "match_method": "pending_review",
        }

    # Re-read the patient under the operation session (the request session was
    # closed) for the detached-citizen identity fields.  For ACCEPT_MATCH the
    # reviewed citizen is already recorded on the claim; no patient read needed.
    def _operation(session: Session) -> dict[str, object]:
        if canonical_decision == "ACCEPT_MATCH":
            outcome = mpi_resolver.confirm_reviewed_match(
                session,
                claim_id=claim_id,
                reason=reason,
                reviewer_user_id=current_user.id,
            )
            return {
                "claim_id": claim_id,
                "status": "confirmed",
                "decision": canonical_decision,
                "previous_citizen_id": outcome.citizen.id,
                "new_citizen_ulid": outcome.citizen.citizen_ulid,
                "match_method": outcome.match_method,
            }

        patient = (
            session.query(Patient)
            .filter(Patient.id == local_patient_id, Patient.lab_id == lab_id)
            .first()
        )
        if patient is None:
            raise ValueError("underlying patient missing")

        by = bm = bd = None
        if patient.birth_date:
            by = patient.birth_date.year
            bm = patient.birth_date.month
            bd = patient.birth_date.day

        outcome = mpi_resolver.create_detached_citizen(
            session,
            claim_id=claim_id,
            name=patient.full_name or "",
            phone=patient.phone,
            birth_year=by,
            birth_month=bm,
            birth_day=bd,
            gender=patient.gender,
            claimed_by_user_id=current_user.id,
            rejected_citizen_id=old_citizen_id,
            decision=canonical_decision,
            reason=reason,
        )
        # Materialise BEFORE the commit owned by bounded_retry (expire_on_commit).
        return {
            "claim_id": claim_id,
            "status": "rejected",
            "decision": canonical_decision,
            "previous_citizen_id": old_citizen_id,
            "new_citizen_ulid": outcome.citizen.citizen_ulid,
            "match_method": outcome.match_method,
        }

    def _reconcile() -> dict[str, object] | None:
        return _decision_reconcile(
            claim_id=claim_id, canonical_decision=canonical_decision
        )

    try:
        return bounded_retry(
            _database.SessionLocal, _operation, reconcile=_reconcile
        )
    except ValueError as exc:
        # Unknown decision / claim no longer pending / missing patient.
        if "no longer pending" in str(exc) or "not found" in str(exc):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if "patient missing" in str(exc):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail="MPI review decision could not be committed"
        ) from exc


# ── GET /mpi/citizens/{citizen_ulid}/access — consent-gated citizen read ─────
# Unlike the admin-only projection above, this endpoint is reachable by any
# authenticated actor (doctor, staff). It is gated by the consent layer:
# the caller must hold an active Consent row (scope='read:citizen') for this
# citizen, OR be the citizen themselves (owner bypass), OR supply the
# emergency break-glass header as a doctor.


@router.get("/citizens/{citizen_ulid}/access", response_model=CitizenResponse)
def get_citizen_with_consent(
    citizen_ulid: str,
    current_user: LabUser = Depends(require_consent("read:citizen")),
    db: Session = Depends(get_db),
) -> CitizenResponse:
    """Cross-lab citizen projection, gated by the consent layer.

    Response shape matches the admin endpoint (no raw PII). The difference
    is the authorization model: this route is for doctors/labs acting on
    the subject's behalf with recorded consent, not for administrators.
    """
    citizen = db.query(Citizen).filter(Citizen.citizen_ulid == citizen_ulid).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    merged_into_ulid = None
    if citizen.merged_into_id is not None:
        survivor = citizen.canonical()
        if survivor is not None and survivor.id != citizen.id:
            merged_into_ulid = survivor.citizen_ulid

    return CitizenResponse(
        citizen_ulid=citizen.citizen_ulid,
        nid_verified=citizen.nid_verified,
        birth_year=citizen.birth_year,
        gender=citizen.gender,
        status=citizen.status,
        merged_into_ulid=merged_into_ulid,
        created_at=citizen.created_at,
    )
