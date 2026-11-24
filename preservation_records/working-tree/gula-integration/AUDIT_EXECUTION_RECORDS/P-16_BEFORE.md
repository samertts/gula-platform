# P-16 Pre-Change Package Record (owner numbering = roadmap P-14 / AUD-F16 — MPI identity integrity)

Generated: 2026-11-20T18:06:05Z (UTC)

## Git baseline
- branch: integration/gula-unification-v1
- HEAD: 2206654dc713ea2de8c564a3207dfe05fde23549
- protected sibling HEAD: f478676b6fc375338648dde46fbf076c015a3f91
- staged name-status MD5: 56c524d6ffe9872c3a3ac6eff8c8f203
- staged count: 20
- staged R100 count: 20
- unstaged count: 160
- untracked count: 645
- git diff --check exit: 0

## Protected MD5s
effdfeaf10234678d83b2668c4489552  GOVERNANCE/FINAL_DECISION.md
1a02c01563c93b07a7cdb92c0462bf36  GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md
ea3969d09aaf7b0b28a065838b44a594  GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md

## Target file state (pre-change)
 M backend/app/services/patient_service.py
872d067bac5df11149f06a576d56e8bf  backend/app/services/patient_service.py

## Defect site (current working tree)
def _resolve_mpi(
    db: Session,
    patient: Patient,
    national_id: str | None,
    family_id: str | None,
    user_id: int,
    lab_id: int,
) -> tuple[str | None, str | None]:
    """Resolve MPI identity. Returns (citizen_ulid, match_method)."""
    birth_year = birth_month = birth_day = None
    if patient.birth_date:
        birth_year, birth_month, birth_day = (
            patient.birth_date.year,
            patient.birth_date.month,
            patient.birth_date.day,
        )
    citizen_ulid = None
    mpi_match_method = None
    try:
        outcome = mpi_resolver.resolve_identity(
            db,
            lab_id=lab_id,
            local_patient_id=patient.id,
            name=patient.full_name,
            phone=patient.phone,
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            gender=patient.gender,
            national_id=national_id,
            family_id=family_id,
            claimed_by_user_id=user_id,
        )
        citizen_ulid = outcome.citizen.citizen_ulid
        mpi_match_method = outcome.match_method
    except Exception as mpi_err:
        log_action(
            db,
            action="mpi_resolve_failed",
            resource_type="patient",
            resource_id=patient.id,
            user_id=user_id,
            user_role="system",
            details=f"MPI resolve failed: {type(mpi_err).__name__}: {str(mpi_err)[:200]}",
        )
    return citizen_ulid, mpi_match_method

## Response assembly

    # MPI resolution
    citizen_ulid, mpi_match_method = _resolve_mpi(
        db, patient, national_id, family_id, user_id, lab_id,
    )

    log_action(
        db,
        action="create",
        resource_type="patient",
        resource_id=patient.id,
        user_id=user_id,
        user_role=user_role,
        details=f"Created patient {patient.full_name} (phone={phone})",
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(patient)

    resp = patient_to_dict(patient)
    resp["citizen_ulid"] = citizen_ulid
    resp["mpi_match_method"] = mpi_match_method
    return {"message": "Patient created", "patient": resp}


## production_ready_items
480:    "production_ready_items": 0
600:  "production_ready_items": 0,
