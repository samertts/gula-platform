"""Regression guard: every ORM foreign-key target resolves in registered metadata.

Defect reproduced 2026-11-18: the NR-011 cross-metadata test failed only when
``tests/identity`` was co-collected, because route-only identity model modules
were then imported and registered four FK targets that no ORM table defined:

* ``niam_adaptive_mfa_sessions.session_id -> niam_user_sessions.id`` (typo; the
  canonical table is ``niam_sessions`` and migration 20260723_0002:1240 already
  used it);
* three ``*_id -> niam_identity_authorities.id`` references whose table existed
  in migration 20261114_0001 but had no ORM model.

The failure was a genuine model/migration drift, not a flaky test. Fixes:
corrected FK target, added the missing ORM mirror, and this invariant test.
No test was skipped, weakened or converted to xfail. No database is contacted.
"""

from __future__ import annotations

import pytest
from sqlalchemy import MetaData, Table


def _registered_metadata() -> list[MetaData]:
    """Import the full application surface and return all declarative metadata."""
    import app.main  # registers route-only identity model modules
    from app.care_continuum.base import CareContinuumBase
    from app.citizen_platform.base import CitizenPlatformBase
    from app.clinical.base import ClinicalBase
    from app.database import Base
    from app.ehr.base import EHRBase
    from app.financial.models import FinBase
    from app.governance.base import GovernanceBase
    from app.health_data.base import HealthDataBase
    from app.hospital.base import HospitalBase
    from app.identity.base import IdentityBase
    from app.national.base import NationalBase
    from app.national_data.base import DataPlatformBase
    from app.nhdw.base import NHDWBase
    from app.nursing.base import NursingBase
    from app.pharmacy.base import PharmacyBase
    from app.radiology.base import RadiologyBase
    from app.trust.base import TrustBase

    return [
        Base.metadata,
        IdentityBase.metadata,
        NationalBase.metadata,
        EHRBase.metadata,
        CitizenPlatformBase.metadata,
        ClinicalBase.metadata,
        HealthDataBase.metadata,
        TrustBase.metadata,
        GovernanceBase.metadata,
        CareContinuumBase.metadata,
        HospitalBase.metadata,
        DataPlatformBase.metadata,
        NHDWBase.metadata,
        NursingBase.metadata,
        PharmacyBase.metadata,
        RadiologyBase.metadata,
        FinBase.metadata,
    ]


def test_every_foreign_key_target_resolves() -> None:
    tables: dict[str, Table] = {}
    for metadata in _registered_metadata():
        for name, table in metadata.tables.items():
            tables.setdefault(name, table)

    dangling: list[str] = []
    for table_name, table in tables.items():
        for foreign_key in table.foreign_keys:
            target_table = foreign_key.target_fullname.split(".", 1)[0]
            if target_table not in tables:
                dangling.append(
                    f"{table_name}.{foreign_key.parent.name} -> {foreign_key.target_fullname}"
                )

    assert not dangling, "unresolved ORM FK target(s): " + "; ".join(sorted(dangling))


def test_adaptive_mfa_session_references_canonical_session_table() -> None:
    from app.identity.adaptive_auth.models import AdaptiveMFASession
    from app.identity.models.session import UserSession

    foreign_keys = list(AdaptiveMFASession.__table__.c.session_id.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == f"{UserSession.__tablename__}.id"


@pytest.mark.parametrize(
    "table_name",
    ["niam_identity_authorities", "niam_sessions", "niam_adaptive_mfa_sessions"],
)
def test_required_identity_tables_registered(table_name: str) -> None:
    from app.identity.base import IdentityBase

    assert table_name in IdentityBase.metadata.tables
