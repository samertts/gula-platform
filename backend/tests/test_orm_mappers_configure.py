"""NR-073 — every mapper in the application must configure.

SQLAlchemy resolves `relationship("Target")` strings lazily, at mapper
configuration, and configuration is **global**: the first ORM use of any model
configures every mapper the registry cascade reaches. So one unresolvable
relationship string is not a local problem with one model. It is an
`InvalidRequestError` waiting for whichever query happens to run first.

That is what `app/nhdw/models.py` held. It declared 22 relationships against
`Patient`, `HospitalDepartment`, `HospitalMaster`, `Room`, `Bed` and `Clinic` --
all of which live in other declarative bases, so the NHDW registry never
contained those names:

    InvalidRequestError: When initializing mapper Mapper[Admission(nhdw_admissions)],
    expression 'Patient' failed to locate a name ('Patient')

`nhdw_admissions` **is** built, and `nhdw_router` is registered at
`factory.py:733`, so this was not the unbuilt-table class NR-067 tracks. It was
a built table behind a live route whose ORM could not be used at all -- a class
none of the existing guards could see, because every one of them asks "is the
table built?" and the answer was yes.

The guard is the cheapest possible statement of the invariant: build the
application the way it is built at runtime, then ask SQLAlchemy to configure
every mapper. If any relationship string does not resolve, this fails here
instead of on a user's request.

Deliberately not marked `integration`: it needs no database. It needs the real
import graph, which is the only thing that makes the defect visible -- importing
a subset of models leaves the broken registry unconfigured and passes.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import configure_mappers


@pytest.fixture(scope="module")
def application():
    """The real factory, because a partial import cannot reproduce the defect."""
    from app.factory import create_app

    return create_app()


def test_every_mapper_in_the_application_configures(application) -> None:
    """One unresolvable relationship string breaks ORM use everywhere.

    The failure message names the mapper and the unresolved expression, which is
    usually enough to find the declaration without a stack trace: look for a
    `relationship("Name")` whose target is defined on a different declarative
    base from the model declaring it.
    """
    assert application is not None
    try:
        configure_mappers()
    except Exception as exc:
        pytest.fail(
            "SQLAlchemy could not configure every mapper, so the first ORM "
            "query to run in this process would raise instead of returning "
            "rows -- whichever query that happens to be, in whichever module. "
            f"{type(exc).__name__}: {exc}"
        )


# A second, static check was written here and then deleted rather than shipped.
#
# It tried to state the root cause structurally: flag any `relationship("X")`
# whose target is neither defined nor imported in the same module. Against this
# repository it reported **36 offenders while `configure_mappers()` passed** --
# every one a false positive, because a relationship to a class in the same
# declarative base but a different module resolves through the shared registry
# and is entirely legal.
#
# Shipping it would have contradicted ADR-027 in the same commit that cites it:
# `configure_mappers()` performs the real resolution, so a static approximation
# beside it is a second source of truth that is wrong more often than it is
# right. The executed check is the authoritative one, and it is enough.

