"""NR-147 — the request body does not get to choose the laboratory.

NR-146's audit of one service module found 41 functions shaped
`create_x(db, data) -> X(**data)`, where `data` is the request body and X
carries lab_id. Repairing 41 call sites is the change the next `create_*`
function silently undoes, so the tenant is defended where all of them pass:
`shared/models/base.py::TenantMixin`, the mixin that declares the column.

THESE TESTS MATTER MORE THAN USUAL. The full backend suite passes unchanged
with the guard active (3295 passed), which is the blast-radius evidence -- but
it also means no production path currently trips it. Nothing else proves the
guard fires. This module is that proof.

It is defence in depth, not authorization: it answers only "is a request
writing into a laboratory other than the authenticated caller's". Outside a
request there is no authenticated tenant to contradict, so it is inert -- which
is exactly why it must never be the only control.
"""
from __future__ import annotations

import pytest

from shared.models.tenant_context import (
    CrossTenantWriteRefused,
    check_tenant_write,
    cross_tenant,
    cross_tenant_reason,
    current_lab_id,
)

LAB_A = 7101
LAB_B = 7202


@pytest.fixture()
def as_lab_a():
    """A request authenticated as Lab A, torn down afterwards."""
    token = current_lab_id.set(LAB_A)
    try:
        yield LAB_A
    finally:
        current_lab_id.reset(token)


# ─── the guard fires ────────────────────────────────────────────────────────

def test_a_a_matching_tenant_is_allowed(as_lab_a):
    """Positive control. Without it, a guard that refused everything would pass
    every negative test below and look correct."""
    assert check_tenant_write("Model", LAB_A) == LAB_A


def test_b_a_foreign_tenant_is_refused(as_lab_a):
    with pytest.raises(CrossTenantWriteRefused) as exc:
        check_tenant_write("PrimaryCareEncounter", LAB_B)
    assert exc.value.attempted == LAB_B
    assert exc.value.actual == LAB_A
    assert "PrimaryCareEncounter" in str(exc.value)


def test_c_the_refusal_says_how_to_declare_a_legitimate_case(as_lab_a):
    """A refusal that does not tell you the escape gets worked around badly."""
    with pytest.raises(CrossTenantWriteRefused) as exc:
        check_tenant_write("Model", LAB_B)
    assert "cross_tenant" in str(exc.value)


def test_d_none_is_left_alone(as_lab_a):
    """A row with no tenant yet is not a contradiction."""
    assert check_tenant_write("Model", None) is None


# ─── inert where there is no truth to enforce ───────────────────────────────

def test_e_outside_a_request_anything_passes():
    """Workers, migrations, CLI and tests have no authenticated tenant.

    Asserted rather than left implicit, because this is the guard's most
    important limitation: it cannot police a value it has no truth for, and a
    reader must not mistake it for a complete control.
    """
    assert current_lab_id.get() is None
    assert check_tenant_write("Model", LAB_B) == LAB_B


# ─── the explicit escape ────────────────────────────────────────────────────

def test_f_a_declared_cross_tenant_write_is_allowed(as_lab_a):
    with cross_tenant("nightly national reconciliation"):
        assert check_tenant_write("Model", LAB_B) == LAB_B


def test_g_the_escape_closes_again(as_lab_a):
    """Scoped, not a latch. A leaked escape would disable the guard silently."""
    with cross_tenant("import"):
        check_tenant_write("Model", LAB_B)
    assert cross_tenant_reason() is None
    with pytest.raises(CrossTenantWriteRefused):
        check_tenant_write("Model", LAB_B)


def test_h_the_escape_closes_even_when_the_body_raises(as_lab_a):
    with pytest.raises(ValueError), cross_tenant("import"):
        raise ValueError("boom")
    assert cross_tenant_reason() is None
    with pytest.raises(CrossTenantWriteRefused):
        check_tenant_write("Model", LAB_B)


@pytest.mark.parametrize("reason", ["", "   ", None])
def test_i_the_escape_requires_a_real_reason(reason):
    """The reason is what a reviewer reads when judging the exception."""
    with pytest.raises(ValueError), cross_tenant(reason):
        pass


# ─── wired to the mixin, and to the one contextvar ──────────────────────────

def test_j_the_validator_is_registered_with_sqlalchemy_for_lab_id():
    """The decorator, not just the method.

    A plain method named `_validate_lab_id` would look right and do nothing;
    what makes it a control is SQLAlchemy's @validates registration. Asserted
    against the mapper rather than the source, so a renamed or undecorated
    method fails here. (test_k and test_l prove the behaviour end to end; this
    one names the mechanism so a failure says which part broke.)
    """
    from app.care_continuum.models.primary_care import PrimaryCareEncounter
    from sqlalchemy import inspect as sa_inspect

    validators = sa_inspect(PrimaryCareEncounter).validators
    assert "lab_id" in validators, (
        "TenantMixin's @validates('lab_id') is no longer registered on the "
        "mapper, so the tenant guard does not run at all (NR-147)"
    )


def test_k_a_real_tenant_scoped_model_refuses_a_foreign_lab(as_lab_a):
    """End to end through SQLAlchemy, on a model that actually uses the mixin."""
    from app.care_continuum.models.primary_care import PrimaryCareEncounter

    assert PrimaryCareEncounter(lab_id=LAB_A).lab_id == LAB_A
    with pytest.raises(CrossTenantWriteRefused):
        PrimaryCareEncounter(lab_id=LAB_B)


def test_l_the_mixin_guard_also_covers_reassignment(as_lab_a):
    """NR-146's second defect: a body moving a row to another laboratory."""
    from app.care_continuum.models.primary_care import PrimaryCareEncounter

    row = PrimaryCareEncounter(lab_id=LAB_A)
    with pytest.raises(CrossTenantWriteRefused):
        row.lab_id = LAB_B


def test_m_there_is_exactly_one_tenant_contextvar():
    """database.py must not declare a second one that drifts (NR-134's lesson)."""
    from app.database import _lab_id_var

    assert _lab_id_var is current_lab_id, (
        "backend/app/database.py no longer shares shared.models.tenant_context's "
        "variable; the correlation context and the guard can now disagree (NR-147)"
    )


def test_n_the_setter_is_still_the_authenticated_row():
    """The tenant must come from the user record, never from a token claim."""
    import inspect

    from app.security import dependencies

    source = inspect.getsource(dependencies)
    assert "_lab_id_var.set(user.lab_id)" in source, (
        "the request tenant is no longer set from the authenticated user's own "
        "row; if it now comes from a token claim or a header, the guard is "
        "comparing a client-supplied value against itself (NR-147)"
    )
