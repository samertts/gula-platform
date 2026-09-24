"""NR-003 regression: the canonical drug identity contract, service layer.

Covers the immutability guarantees in docs/pharmacy-platform/CANONICAL_DRUG_CONTRACT.md
§10 that are enforced in application code. The database-level guarantees
(UUID4 generation, NOT NULL, UNIQUE, backfill idempotency, PK preservation) are
proven separately against real PostgreSQL, because a SQLite create_all schema
cannot demonstrate them.
"""

from __future__ import annotations

from typing import Any

import pytest
from app.models.lab import Lab
from app.pharmacy.models import DrugCatalog
from app.pharmacy.services import IMMUTABLE_CATALOG_IDENTITY_FIELDS, PharmacyService


def _lab(db: Any) -> Any:
    lab = Lab(name="Identity Contract Lab", lab_type="pharmacy")
    db.add(lab)
    db.flush()
    return lab


def _service(db: Any, lab: Any) -> PharmacyService:
    return PharmacyService(db=db, user_id=None, lab_id=lab.id)


def _drug(svc: PharmacyService, code: str = "IDENT-001") -> DrugCatalog:
    return svc.create_drug(
        {
            "drug_code": code,
            "drug_name": "Synthetic Identity Drug",
            "dosage_form": "tablet",
            "is_active": True,
        }
    )


def test_identity_fields_are_declared_immutable() -> None:
    """The contract's immutable set must include both identity forms."""
    assert "id" in IMMUTABLE_CATALOG_IDENTITY_FIELDS
    assert "drug_id" in IMMUTABLE_CATALOG_IDENTITY_FIELDS
    # drug_code is a mutable business code (contract §4), never an identity.
    assert "drug_code" not in IMMUTABLE_CATALOG_IDENTITY_FIELDS


def test_client_cannot_choose_the_internal_identity_at_creation(db: Any) -> None:
    lab = _lab(db)
    svc = _service(db, lab)
    drug = svc.create_drug(
        {
            "drug_code": "IDENT-CHOOSE",
            "drug_name": "Synthetic",
            "dosage_form": "tablet",
            "id": "client-supplied-identity",
        }
    )
    assert drug.id != "client-supplied-identity"


def test_update_rejects_an_attempt_to_change_the_internal_identity(db: Any) -> None:
    lab = _lab(db)
    svc = _service(db, lab)
    drug = _drug(svc, "IDENT-UPD-1")
    original = drug.id

    with pytest.raises(ValueError, match="immutable"):
        svc.update_drug(drug.id, {"id": "reassigned"})

    assert svc.get_drug(original) is not None


def test_update_rejects_an_attempt_to_change_the_public_drug_id(db: Any) -> None:
    lab = _lab(db)
    svc = _service(db, lab)
    drug = _drug(svc, "IDENT-UPD-2")

    with pytest.raises(ValueError, match="drug_id"):
        svc.update_drug(drug.id, {"drug_id": "00000000-0000-4000-8000-000000000000"})


def test_business_fields_remain_updatable(db: Any) -> None:
    """Rejecting identity changes must not freeze ordinary catalog data."""
    lab = _lab(db)
    svc = _service(db, lab)
    drug = _drug(svc, "IDENT-UPD-3")

    updated = svc.update_drug(drug.id, {"drug_name": "Renamed Synthetic Drug"})

    assert updated is not None
    assert updated.drug_name == "Renamed Synthetic Drug"
    assert updated.id == drug.id


def test_clinical_rules_do_not_key_on_the_mutable_business_code(db: Any) -> None:
    """Contract §7: a business-code edit must never detach a clinical rule.

    Asserted structurally: the substitution rule's authoritative relationship is
    a foreign key to the catalog's internal key, not a copied drug_code.
    """
    from app.pharmacy.models import DrugSubstitutionRule

    fk_columns = {
        column.name
        for column in DrugSubstitutionRule.__table__.columns
        if column.foreign_keys
        and any(fk.column.table.name == "pharmacy_drug_catalog" for fk in column.foreign_keys)
    }
    assert fk_columns == {"original_drug_catalog_id", "alternative_drug_catalog_id"}
    assert "drug_code" not in {c.name for c in DrugSubstitutionRule.__table__.columns}
