"""No ORM column may disagree with the database about being a boolean.

This guard exists because of a specific, total outage.  Migration
``20260716_0015`` created ``oauth2_clients.is_active``,
``oauth2_clients.is_confidential``, ``oauth2_tokens.is_revoked`` and
``service_accounts.is_active`` as ``sa.Boolean()``.  All four ORM models
declared them ``Integer``.  Every comparison the OAuth2 routes emitted was
therefore ``is_active = 1`` against a boolean column, which PostgreSQL rejects
outright::

    operator does not exist: boolean = integer

The consequence was not a subtle wrong answer -- it was a hard 500 on
``/oauth2/token``, ``/oauth2/introspect``, ``/oauth2/revoke`` and
``/oauth2/authorize``.  The entire OAuth2/OIDC provider was non-functional
against the migrated schema, and no test caught it because the suites that
covered these routes built their tables from the ORM with ``create_all``, where
Integer and Boolean both become a usable column and the drift cannot exist.

That is the whole point of this file: the mismatch is only observable against a
database built by migrations, so the assertion is made there.

Scope is deliberately narrow.  Only the boolean/non-boolean disagreement is
reported, because that is the class that produces invalid SQL.  Width and
affinity differences (``Text`` vs ``String(500)``, ``Integer`` vs
``BigInteger``) are real drift but they do not break a query, and folding them
in here would bury the class that does behind dozens that do not.
"""

from __future__ import annotations

import importlib

import pytest
from sqlalchemy import Boolean, inspect

from tests.verification import harness

pytestmark = harness.requires_postgres()

# Every declarative base in the platform. Listing them explicitly -- rather than
# scanning for ``declarative_base()`` -- keeps a new base from silently joining
# the platform without appearing in this guard: adding one here is a deliberate
# act, and a base absent from this list makes the coverage assertion below fail.
_BASES: tuple[tuple[str, str], ...] = (
    ("app.database", "Base"),
    ("app.identity.base", "IdentityBase"),
    ("app.radiology.base", "RadiologyBase"),
    ("app.governance.base", "GovernanceBase"),
    ("app.financial.models", "FinBase"),
    ("app.hospital.base", "HospitalBase"),
    ("app.health_data.base", "HealthDataBase"),
    ("app.insurance.domain.models", "InsBase"),
    ("app.clinical.base", "ClinicalBase"),
    ("app.ehr.base", "EHRBase"),
    ("app.national.base", "NationalBase"),
    ("app.care_continuum.base", "CareContinuumBase"),
    ("app.nursing.base", "NursingBase"),
    ("app.document_intelligence.infrastructure.models", "DocIntelBase"),
    ("app.nhdw.base", "NHDWBase"),
    ("app.trust.base", "TrustBase"),
    ("app.pharmacy.base", "PharmacyBase"),
    ("app.national_data.base", "DataPlatformBase"),
)


@pytest.fixture(scope="module")
def Session():
    factory = harness.session_factory()
    yield factory
    harness.dispose(factory)


@pytest.fixture(scope="module")
def survey(Session):
    """Compare every mapped column against the physical column it writes to."""
    import app.main  # importing the app registers every model

    engine = Session.kw["bind"]
    insp = inspect(engine)
    physical = set(insp.get_table_names())

    columns: dict[str, dict[str, object]] = {}
    drift: list[str] = []
    compared: set[str] = set()
    unloadable: list[str] = []

    for module_name, attr in _BASES:
        try:
            base = getattr(importlib.import_module(module_name), attr)
        except Exception as exc:  # pragma: no cover - reported, not swallowed
            unloadable.append(f"{module_name}.{attr}: {type(exc).__name__}: {exc}")
            continue

        for table_name, table in base.metadata.tables.items():
            if table_name not in physical:
                # A mapped table with no physical table is real drift, but it is
                # a different finding with its own guard; conflating the two
                # would let a missing table read as a type mismatch.
                continue
            compared.add(table_name)
            if table_name not in columns:
                columns[table_name] = {
                    c["name"]: c["type"] for c in insp.get_columns(table_name)
                }
            for col in table.columns:
                physical_type = columns[table_name].get(col.name)
                if physical_type is None:
                    continue
                if isinstance(col.type, Boolean) != isinstance(physical_type, Boolean):
                    drift.append(
                        f"{table_name}.{col.name}: "
                        f"ORM={type(col.type).__name__} "
                        f"physical={physical_type} "
                        f"[{module_name}.{attr}]"
                    )

    return {
        "drift": sorted(drift),
        "compared": compared,
        "physical": physical,
        "unloadable": unloadable,
    }


def test_every_declarative_base_is_importable(survey):
    """A base this guard cannot import is a base it cannot check.

    Without this, an ImportError would silently shrink coverage and the drift
    assertion below would pass by looking at less.
    """
    assert survey["unloadable"] == []


def test_the_guard_actually_covers_the_platform(survey):
    """Guard against the guard passing because it compared almost nothing.

    The floor is deliberately well below the ~407 tables currently compared, so
    that ordinary growth does not trip it while a collapse in coverage does.
    """
    assert len(survey["compared"]) > 350, (
        f"only {len(survey['compared'])} of {len(survey['physical'])} physical "
        "tables were compared; this guard is no longer measuring the platform"
    )


def test_no_column_disagrees_with_the_database_about_being_boolean(survey):
    assert survey["drift"] == [], (
        "ORM/physical boolean type drift -- every comparison these columns "
        "appear in risks `operator does not exist: boolean = integer`:\n  "
        + "\n  ".join(survey["drift"])
    )
