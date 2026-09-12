"""NR-065 — a national capability may not quietly become a laboratory capability.

NR-065 asked which tenancy the 15 untenanted national orchestration tables should
carry. The earlier answer was "undecided among organization, facility,
governorate and national", reached from inside `task_engine` and
`workflow_runtime` alone. §44 blocks only where evidence is *insufficient*, so
this file records what the wider platform actually proves. One of the four
options is now eliminated, and it is the one that would have been easiest to
reach for.

**Laboratory scope is eliminated, by the authorization model rather than by
preference.** `RoleScopeType` and `MembershipScopeType` -- the two vocabularies
that decide what a role or a membership can be scoped *to* -- are
`organization | facility | department | unit | workspace`. There is no `lab`
member and no `governorate` member. A national artifact keyed by `lab_id` could
therefore not be named by any role assignment: nothing could be granted over it,
and nothing could be denied over it. That is not a style objection. It is the
difference between an access decision and no access decision at all.

The vocabulary is enforced, not merely declared. `MembershipService._validate_context`
looks the scope up in a mapping of exactly those five members and raises
`Unsupported membership scope` on a miss, and `AuthorizationServiceV2` takes the
assignment's `scope_type` from the **role**, never from the caller. All of the
tables behind it (`niam_role_assignments`, `niam_memberships`,
`niam_organizations`) are migration-backed.

**Organization is the mandatory root.** `niam_role_assignments.organization_id`
is `nullable=False`; `facility_id`, `department_id`, `unit_id` and `workspace_id`
are nullable narrowings beneath it. Every one is a ULID `String(26)` into a
`niam_*` table. `TenantMixin.lab_id` is an `Integer` into `labs.id` -- so
adopting it on a national table is not only unnameable by a role, it is a
type-level mismatch with the scope columns themselves.

So the remaining NR-065 question is narrowed, not answered: whether national
orchestration is scoped at the organization root or is genuinely national
(unscoped) is still a decision with clinical and jurisdictional consequences, and
§44 reserves it. What this file prevents is the drift that would make that
decision for us by default.

**Blanket tenancy would be equally wrong**, which is why this guard forbids one
specific adoption rather than requiring a column. `app/national/ecosystem` has
six built tables and none of them carry tenancy: it is an external partner
registry (partners, credentials, certificates, rate limits, agreements), and the
partners it registers sit outside any tenant by definition. Making those rows
tenant-scoped would be a modelling error, not a hardening.

**The one existing exception is declared rather than excused.** Of 113 tables in
`app/national`, exactly two carry `lab_id`: `national_search_saved_searches` and
`national_search_results`. Both are built and both filter on it. What they scope
is a user's own saved searches and their results -- a laboratory-local
convenience that happens to live under `app/national/`, not a national
capability wearing lab tenancy. The ledger may shrink. It may never grow.
"""

from __future__ import annotations

import ast
import collections
import types

from app.identity.models.authorization import RoleAssignment, RoleScopeType
from app.identity.models.membership import MembershipScopeType
from app.identity.services.membership_service import (
    MembershipService,
    MembershipValidationError,
)

from tests.orm_resolution import APP, BACKEND, built_tables, parse

NATIONAL = APP / "national"

#: The scope vocabulary, asserted as a set rather than trusted as an import.
#: NR-065's elimination of laboratory scope rests entirely on what is *absent*
#: here, and an absence is only evidence while the presence is pinned.
CANONICAL_SCOPES = frozenset(
    {"organization", "facility", "department", "unit", "workspace"}
)

#: Scope names that must never appear. `lab` would re-open NR-065. `governorate`
#: is a real Iraqi administrative level, but there is no governorate entity for a
#: scope to point at: `niam_organizations.governorate` is a nullable `String(50)`
#: attribute of an organization, so a governorate is a property of the scope root
#: rather than a level of it. Adding either as a scope is a hierarchy decision,
#: not a keyword, and belongs in NR-065 before it belongs in an enum.
FORBIDDEN_SCOPES = frozenset({"lab", "laboratory", "governorate", "tenant"})

#: The mandatory scope root and its optional narrowings, from
#: `niam_role_assignments`. If organization ever became optional, "organization
#: is the root" would stop being true and NR-065's narrowing would need redoing.
SCOPE_ROOT = "organization_id"
SCOPE_NARROWINGS = ("facility_id", "department_id", "unit_id", "workspace_id")

#: The only tables under `app/national` that may carry laboratory tenancy.
#: See the module docstring: user-local saved searches, not a national
#: capability. May shrink, may never grow.
DECLARED_LAB_SCOPED_NATIONAL_TABLES = {
    "national_search_saved_searches": "app/national/search_platform/infrastructure/models.py",
    "national_search_results": "app/national/search_platform/infrastructure/models.py",
}


def _national_models() -> list[tuple[str, str, str, list[str], list[str]]]:
    """(module, class, table, base names, assigned column names) for app/national."""
    found: list[tuple[str, str, str, list[str], list[str]]] = []
    for path in sorted(NATIONAL.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = parse(path)
        if tree is None:
            continue
        module = str(path.relative_to(BACKEND))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            table = None
            columns: list[str] = []
            for stmt in cls.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    if target.id == "__tablename__" and isinstance(stmt.value, ast.Constant):
                        table = stmt.value.value
                    else:
                        columns.append(target.id)
            if table:
                bases = [b.id for b in cls.bases if isinstance(b, ast.Name)]
                found.append((module, cls.name, table, bases, columns))
    return found


def test_the_national_model_scan_still_sees_its_surface() -> None:
    """Guard the guard: a scan that found nothing would allow everything."""
    models = _national_models()
    assert len(models) >= 100, (
        f"only {len(models)} ORM models found under app/national; the scan has "
        "drifted and the tenancy ledger below would be vacuously satisfied"
    )


def test_the_scope_vocabulary_has_no_laboratory_member() -> None:
    """The proof NR-065's elimination rests on.

    Both vocabularies must stay identical and must stay free of a laboratory
    scope. If a `lab` member is ever added, laboratory scope stops being
    unnameable by a role assignment and NR-065 has to be argued again from the
    beginning rather than silently inherited.
    """
    for enum in (RoleScopeType, MembershipScopeType):
        members = {member.value for member in enum}
        assert members == CANONICAL_SCOPES, (
            f"{enum.__name__} is no longer the canonical scope vocabulary "
            f"({sorted(members)}); NR-065 eliminated laboratory tenancy for "
            "national orchestration from exactly this set, so a change here "
            "invalidates that conclusion rather than extending it"
        )
        assert members & FORBIDDEN_SCOPES == set(), (
            f"{enum.__name__} gained a forbidden scope: "
            f"{sorted(members & FORBIDDEN_SCOPES)}"
        )


def test_an_unsupported_scope_is_refused_rather_than_stored() -> None:
    """The vocabulary is enforced, not decorative -- executed, not inferred.

    `_validate_context` is the only place a membership scope is checked before a
    row is written. If it ever accepted an unknown scope, `scope_type` would
    become a free-text column the caller controls, and every claim above about
    what a role can be scoped to would be a claim about an enum nobody consults.
    """
    active_organization = types.SimpleNamespace(status="active", is_active=True)
    session = types.SimpleNamespace(scalar=lambda _statement: active_organization)
    service = MembershipService(session)  # type: ignore[arg-type]

    try:
        service._validate_context("ORG00000000000000000000001", "lab", None, None, None, None)
    except MembershipValidationError as exc:
        assert "Unsupported membership scope" in str(exc), (
            f"an unknown scope was rejected, but for the wrong reason: {exc}"
        )
    else:
        raise AssertionError(
            "MembershipService._validate_context accepted scope_type='lab'. "
            "scope_type is a String(30) the caller supplies, so nothing else "
            "stops an arbitrary scope from being persisted and later trusted."
        )

    # And the five canonical scopes are still reachable: a guard that rejected
    # everything would pass the assertion above and break the platform.
    try:
        service._validate_context("ORG00000000000000000000001", "organization", None, None, None, None)
    except MembershipValidationError as exc:  # pragma: no cover - regression only
        raise AssertionError(
            f"the canonical `organization` scope is now refused as well: {exc}"
        ) from exc


def test_organization_is_the_mandatory_scope_root() -> None:
    """Read off the mapped table, not off the source text.

    NR-065's narrowing says the scope tree has one required root with optional
    narrowings beneath it. That shape is what makes "organization or national"
    the remaining question; if organization became optional there would be no
    root to choose.
    """
    columns = RoleAssignment.__table__.c
    assert not columns[SCOPE_ROOT].nullable, (
        "niam_role_assignments.organization_id is nullable now. The scope tree "
        "has no mandatory root, so a role assignment can exist outside every "
        "organization and NR-065's narrowing no longer holds"
    )
    optional = [name for name in SCOPE_NARROWINGS if not columns[name].nullable]
    assert optional == [], (
        "these scope narrowings became mandatory, which forces every role "
        f"assignment down to the narrowest level: {optional}"
    )


def test_no_national_capability_adopts_laboratory_tenancy() -> None:
    """The ratchet, with the one real exception named rather than waived."""
    adopters: dict[str, str] = {}
    for module, _cls, table, bases, columns in _national_models():
        if "lab_id" in columns or "TenantMixin" in bases:
            adopters[table] = module

    appeared = {
        table: module
        for table, module in adopters.items()
        if DECLARED_LAB_SCOPED_NATIONAL_TABLES.get(table) != module
    }
    assert appeared == {}, (
        "these tables under app/national now carry laboratory tenancy "
        "(lab_id or TenantMixin). No role assignment can be scoped to a lab -- "
        "RoleScopeType has no such member -- so nothing can be granted or "
        "denied over these rows. Scope them at the organization root, or "
        f"establish that the capability is genuinely lab-local: {appeared}"
    )

    resolved = sorted(
        table for table in DECLARED_LAB_SCOPED_NATIONAL_TABLES if table not in adopters
    )
    assert resolved == [], (
        "these tables no longer carry lab_id; remove them from the ledger so "
        f"the ratchet keeps its grip: {resolved}"
    )


def test_the_declared_exception_is_built_and_therefore_real() -> None:
    """An exception granted to an unbuilt table would be an exception to nothing.

    `search_platform` is allowed to keep `lab_id` because it is a shipped,
    migration-backed, laboratory-local capability. If its tables stopped being
    built, the exception would be protecting a hypothetical -- and the honest
    move would be to withdraw it, not to keep it on the strength of the source
    file alone.
    """
    built = built_tables()
    missing = sorted(t for t in DECLARED_LAB_SCOPED_NATIONAL_TABLES if t not in built)
    assert missing == [], (
        "the laboratory-tenancy exception is granted to tables no migration "
        f"builds, so it protects nothing and should be withdrawn: {missing}"
    )


def test_the_untenanted_national_surface_is_still_the_open_question() -> None:
    """Keep NR-065's scale visible so the decision is not quietly forgotten.

    The point of measuring is that this is not two packages and fifteen tables.
    It is most of `app/national`. A number that collapsed would mean either the
    surface was resolved -- which is the outcome NR-065 wants, and should be
    recorded deliberately -- or that the scan stopped seeing it.
    """
    scoping = ("lab_id", "tenant_id", "organization_id", "facility_id", "governorate_id")
    untenanted = [
        table
        for _module, _cls, table, _bases, columns in _national_models()
        if not any(name in columns for name in scoping)
    ]
    by_package = collections.Counter(
        module.split("/")[2]
        for module, _cls, table, _bases, columns in _national_models()
        if not any(name in columns for name in scoping)
    )
    assert len(untenanted) >= 60, (
        f"only {len(untenanted)} untenanted national tables found across "
        f"{len(by_package)} packages; NR-065 measured a far larger surface, so "
        "either it was resolved -- record that -- or this scan has drifted"
    )
