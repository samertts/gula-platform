"""NR-089 — a soft-delete mixin declared, and never mixed in. Twice.

`app/trust/base.py` defines `TrustSoftDeleteMixin` with `is_deleted` and
`deleted_at`, a `soft_delete()`, a `restore()` and an `is_active` property. Then::

    class TrustBaseEntity(TrustTimestampMixin, TrustBase):

The soft-delete mixin is not in that list. Executed::

    TrustBaseEntity.__bases__                     ['TrustTimestampMixin', 'Base']
    TrustSoftDeleteMixin in ConsentRecord.__mro__  False
    ConsentRecord.is_deleted                       AttributeError
    ConsentRecord.deleted_at                       AttributeError

**And six service methods filter on it anyway.** `app/trust/services.py` lines 88,
105, 116, 136, 157 and 223 build `Model.is_deleted.is_(None)`, which raises on
attribute access before any SQL is emitted. Executed against PostgreSQL at
migration head with a real session::

    ConsentService.get_patient_consents(1)  AttributeError: 'ConsentRecord' has no attribute 'is_deleted'
    SovereigntyService.get_all_rules()      AttributeError: 'SovereigntyRule' has no attribute 'is_deleted'

`app/trust/routes.py` calls all six: `verify_consent` (113),
`get_patient_consents` (124), `withdraw_consent` (147), `get_all_rules` (172)
and `verify_document_integrity` (256). So five served routes raise.

**This extends NR-086 rather than correcting it.** That finding recorded
`trust_sovereignty_rules` as ORM SELECT OK / ORM INSERT OK -- the one healthy
trust table -- and said reads are unaffected. Both statements are accurate
*about ORM table operations*. This is a different and earlier barrier, in the
service layer: the one healthy trust table is still unreachable through
`SovereigntyService`, because the failure happens while building the filter.

The physical tables have both columns, on all six trust tables, nullable and
with no default (migration `20260716_0013`). That is why NR-080's classification
finds exactly twelve trust columns proposed for DROP -- a second instrument
arriving at the same place.

**The same mixin mistake in governance, with a worse shape.**
`GovernanceSoftDeleteMixin` is likewise never mixed in, and
`app/governance/repositories/base.py::delete` reads::

    if soft and hasattr(entity, "is_deleted"):   ...
    elif soft and hasattr(entity, "is_active"):  ...
    else:                                        self._db.delete(entity)

`soft` defaults to **True**, so for a model carrying neither attribute the
request to soft-delete falls through to a hard `DELETE`. **38 of the 61
governance mapped classes carry neither**, among them `gov_national_audit_events`,
`gov_ai_audit_events`, `gov_health_number_audit`, `gov_merge_proposals`,
`gov_merged_identities`, `gov_professional_licenses` and `gov_emergency_admin`.

That is latent, not live, and the difference was established rather than
assumed: **nothing calls that `delete()`**. The governance router is registered
(`factory.py:683`) and exposes no delete, and no caller exists anywhere in
`app/` -- the one nearby hit, `document_intelligence`, deletes a different model
by raw query. So the guard below pins the caller count at zero: the day someone
wires a governance delete endpoint is the day audit rows start disappearing.

Two guards, because the two instances fail differently. The trust one is about
an attribute that must exist. The governance one is about a caller that must not.
"""

from __future__ import annotations

import ast
import re

from tests.orm_resolution import BACKEND, parse

#: Trust service methods filter on these; the mapped classes must carry them.
TRUST_SERVICES = "app/trust/services.py"

#: `GovernanceRepository.delete` hard-deletes any model lacking both flags, and
#: `soft` defaults to True. Zero callers today. This may not grow.
GOVERNANCE_DELETE_CALLERS = 0


def _trust_model_attribute_uses() -> set[tuple[str, str]]:
    """`(ClassName, attribute)` pairs the trust services read off a model."""
    tree = parse(BACKEND / TRUST_SERVICES)
    assert tree is not None, f"{TRUST_SERVICES} did not parse"
    import app.trust.models as models

    known = {
        name for name in dir(models)
        if isinstance(getattr(models, name, None), type)
        and hasattr(getattr(models, name), "__tablename__")
    }
    found: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in known):
            found.add((node.value.id, node.attr))
    return found


def test_the_trust_service_scan_still_sees_model_attribute_use() -> None:
    """Guard the guard. A scan finding nothing would assert nothing."""
    uses = _trust_model_attribute_uses()
    assert len(uses) >= 12, (
        f"only {len(uses)} model-attribute uses found in {TRUST_SERVICES}; the "
        "scan has drifted and the assertion below would be vacuous"
    )


def test_every_attribute_a_trust_service_filters_on_exists() -> None:
    """The live defect, as a regression rather than a memory.

    An attribute that the mapped class does not carry raises `AttributeError`
    while the query is being *built* -- before SQLAlchemy emits anything, and
    before any of the schema guards in this suite get a chance to look.
    """
    import app.trust.models as models

    missing = sorted(
        f"{cls}.{attr}"
        for cls, attr in _trust_model_attribute_uses()
        if not hasattr(getattr(models, cls), attr)
    )
    assert missing == [], (
        "app/trust/services.py reads attributes the mapped class does not have, "
        "so every method touching them raises AttributeError before emitting "
        f"SQL: {missing}"
    )


def test_nothing_calls_the_governance_repository_delete() -> None:
    """The latent one. `soft=True` hard-deletes 38 of 61 governance models.

    Three of those carry audit rows. Wiring a delete endpoint without first
    giving the models a soft-delete flag turns "archive this" into "destroy the
    audit trail", and the default argument makes that the *quiet* path rather
    than the explicit one.
    """
    pattern = re.compile(r"\.delete\s*\(")
    callers: list[str] = []
    for path in (BACKEND / "app").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = str(path.relative_to(BACKEND))
        if relative == "app/governance/repositories/base.py":
            continue  # the implementation itself
        source = path.read_text()
        if "governance" not in relative:
            continue
        for number, line in enumerate(source.splitlines(), 1):
            if pattern.search(line) and "self._db.delete" not in line:
                callers.append(f"{relative}:{number}")
    assert len(callers) <= GOVERNANCE_DELETE_CALLERS, (
        "a governance repository delete now has a caller. Before this ships, "
        "give the 38 models that carry neither is_deleted nor is_active a "
        "soft-delete flag -- `soft=True` currently falls through to a hard "
        f"DELETE, and gov_national_audit_events is one of them: {callers}"
    )
