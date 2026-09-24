"""NR-070 / NR-072 — authorization, mass assignment and actor integrity.

Three defects on the same two packages, found by the NR-065 Unit 8 caller trace
and fixed together because they fail together:

1. `factory.py` registers `workflow_runtime`, `task_engine` and `intelligence`,
   and none of the three route modules contained a single `require_permission`.
   Every endpoint depended on `get_current_user` alone, so any authenticated
   principal -- a laboratory technician with no national role included -- had
   create/execute/cancel/reassign over the national orchestration surface.
2. `TaskEngineService.update_task` walked the request body with `setattr`,
   excluding only `id`, `created_at` and `version`, which made `created_by`,
   `assigned_to`, `assigned_by` and `status` client-writable.
3. `POST /{task_id}/assign` took `assigned_by` from the body while
   `current_user` sat on the same handler, and `national_task_audit_logs.actor_id`
   -- a column that has existed all along -- was written NULL by every path.

**The permission is not new.** Thirteen national route modules already guard
themselves and all thirteen use exactly `require_permission("system:admin")`, at
the router rather than the handler; no other permission string appears anywhere
in `app/national`. All seven platform siblings put their own `/health` endpoint
under that same router dependency, so guarding `/national/workflows/health` is
the convention rather than an exception to it. Inventing a
`national:orchestration:*` vocabulary would have created a second taxonomy for
one package and left `system:admin` meaning something different either side of
it.

What that scopes it to, stated rather than implied: `system:admin` is held by
`master_admin` and by no other role in `EXTENDED_ROLE_PERMISSIONS`. So this is
the *tightest* reading available from repository evidence, not a comfortable
middle. If national orchestration should later be reachable by `ministry_admin`,
that is a deliberate widening of a role's permission set -- a human decision
under CLAUDE.md's authorization boundary -- and not something to pre-empt by
picking a looser permission here.

Structure of the proof below, in the order the evidence has to arrive:

* the permission is attached to every *route of the running application*, read
  out of the app's own dependant tree rather than grepped from a file -- a
  file-level grep passes on a module that imports `require_permission` and
  forgets one handler;
* a principal without the permission is refused (negative);
* a principal holding it is served a 200 (positive);
* the service rejects the fields the caller does not own;
* the actor written to the audit log is the server's, not the body's.

Two things this had to be built around, both found by running it:

* the application registers its routers from the lifespan and FastAPI stores
  each one as an opaque `_IncludedRouter`, so `create_app().routes` is 7 entries
  and `app.routes` after startup is 130. The real surface is 2109 routes and
  only a recursive walk through `original_router` reaches it. A structural guard
  written the obvious way would have found zero routes and passed;
* `/intelligence` is claimed by **two** routers -- `app/national/intelligence`
  (this finding) and `app/command_intelligence`, registered forty lines apart in
  `factory.py`, the latter guarded with `dashboard:read`. Selecting routes by
  path prefix therefore mixes two unrelated modules together, so everything
  below selects by the endpoint's defining module instead.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from app.national.task_engine.application.service import TaskEngineService
from app.national.task_engine.domain.entities import NationalTask
from app.national.task_engine.domain.enums import TaskPriority, TaskStatus
from app.national.task_engine.exceptions import TaskFieldNotUpdatableError
from app.security.dependencies import get_current_user

from tests.orm_resolution import every_route

#: The one permission `app/national` uses. Asserted rather than assumed by
#: `test_the_canonical_permission_is_the_only_one_national_uses`.
CANONICAL = "system:admin"

#: The three route modules NR-070 and NR-072 cover, identified by module rather
#: than by URL prefix: `/intelligence` is claimed by `app/command_intelligence`
#: as well, and that router is guarded with a different permission.
GUARDED_MODULES = (
    "app.national.task_engine.api.routes",
    "app.national.workflow_runtime.api.routes",
    "app.national.intelligence.routes",
)


# ── reading the dependency out of the application ────────────────────────────

def _required_permissions(route: Any) -> set[str]:
    """Permission strings `require_permission` contributes to one route.

    `require_permission` returns a closure named `checker` that closes over the
    permission string. Walking the dependant tree finds it wherever it was
    attached -- router-level `dependencies=[...]`, a handler default, or a
    nested router -- which is the difference between proving the running
    application is guarded and proving a file mentions the word.
    """
    found: set[str] = set()

    def walk(dependant: Any) -> None:
        call = getattr(dependant, "call", None)
        if getattr(call, "__name__", "") == "checker":
            for cell in getattr(call, "__closure__", None) or ():
                try:
                    value = cell.cell_contents
                except ValueError:  # pragma: no cover - empty cell
                    continue
                if isinstance(value, str):
                    found.add(value)
        for sub in getattr(dependant, "dependencies", []):
            walk(sub)

    walk(route.dependant)
    return found


# `every_route` -- the recursion through `_IncludedRouter.original_router` that
# this file needed first -- now lives in `tests/orm_resolution.py` with the rest
# of the resolution logic. It was copied here once and immediately became the
# second place a reachability question was answered; NR-079 is what happens when
# two answers drift.


@pytest.fixture()
def application(client):
    """The application **after** startup, which is the only one that has routes.

    `create_app()` on its own returns an app with seven routed paths: this
    platform registers its routers from the lifespan. A structural check written
    against a freshly-constructed app finds nothing and passes green -- the same
    shape as the defects this file exists for. Depending on `client` is what
    runs the lifespan.
    """
    from app.main import app

    total = len(list(every_route(app.routes)))
    assert total > 1000, (
        f"the application came up with only {total} routes; every assertion in "
        "this file would be vacuous"
    )
    return app


def _module_of(route: Any) -> str:
    return getattr(getattr(route, "endpoint", None), "__module__", "")


def _routes_in(application, modules: tuple[str, ...]) -> list[Any]:
    return [r for r in every_route(application.routes) if _module_of(r) in modules]


def test_the_orchestration_surface_is_actually_registered(application) -> None:
    """Guard the guard. Finding no routes would make every assertion vacuous."""
    routes = _routes_in(application, GUARDED_MODULES)
    assert len(routes) >= 70, (
        f"only {len(routes)} routes found in {GUARDED_MODULES}; the scan has "
        "drifted and the authorization assertions below would pass on nothing"
    )


def test_every_orchestration_route_requires_the_canonical_permission(application) -> None:
    """NR-070 / NR-072, proved against the app rather than the source."""
    unguarded = sorted(
        f"{sorted(route.methods or [])} {route.path}"
        for route in _routes_in(application, GUARDED_MODULES)
        if CANONICAL not in _required_permissions(route)
    )
    assert unguarded == [], (
        "these national orchestration routes carry no "
        f"`require_permission({CANONICAL!r})` in their dependant tree, so any "
        f"authenticated principal reaches them: {unguarded}"
    )


def test_the_canonical_permission_is_the_only_one_national_uses(application) -> None:
    """Reuse is only reuse while the vocabulary stays one word wide.

    Scoped to `app.national.*` by module. If a second permission string appears
    there, the claim that NR-070 was closed by reusing the canonical one stops
    being true and the choice has to be made again deliberately rather than
    inherited.
    """
    vocabulary: set[str] = set()
    for route in every_route(application.routes):
        if _module_of(route).startswith("app.national."):
            vocabulary |= _required_permissions(route)
    assert vocabulary <= {CANONICAL}, (
        "the national surface now requires more than one permission string "
        f"({sorted(vocabulary)}). That may be right, but it is a second "
        "taxonomy and needs deciding rather than accumulating"
    )


def test_the_permission_is_held_by_exactly_one_role() -> None:
    """State the blast radius instead of leaving it to be discovered.

    This is not an argument that only `master_admin` *should* reach national
    orchestration. It records what choosing the canonical permission actually
    grants, so that widening it later is a visible edit here rather than a quiet
    consequence somewhere else.
    """
    from shared.rbac import EXTENDED_ROLE_PERMISSIONS

    holders = sorted(r for r, p in EXTENDED_ROLE_PERMISSIONS.items() if CANONICAL in p)
    assert holders == ["master_admin"], (
        f"the set of roles holding {CANONICAL!r} changed to {holders}. Every "
        "route in this file's scope moved with it"
    )


# ── negative and positive authorization, through the real stack ──────────────

class _Principal:
    """The shape `require_permission` reads: an id and a role, nothing else."""

    def __init__(self, role: str) -> None:
        self.id = 4242
        self.role = role
        self.lab_id = 1
        self.email = f"{role}@example.test"


@pytest.fixture()
def as_role(client):
    from app.main import app

    def _use(role: str):
        app.dependency_overrides[get_current_user] = lambda: _Principal(role)
        return client

    yield _use
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/national/tasks/"),
        ("get", "/national/tasks/"),
        ("post", "/national/workflows/execute"),
        ("get", "/national/workflows/definitions"),
        ("get", "/national/workflows/health"),
        ("get", "/intelligence/ai/models"),
    ],
)
def test_a_principal_without_the_permission_is_refused(as_role, method, path) -> None:
    """NEGATIVE. A technician is authenticated and still has no business here.

    `/national/workflows/health` is in the list on purpose: all seven national
    platform siblings put their own `/health` under the router dependency, so
    matching them is the convention rather than an oversight.
    """
    caller = as_role("technician")
    kwargs = {"json": {"title": "t", "type": "t"}} if method == "post" else {}
    response = getattr(caller, method)(path, **kwargs)
    assert response.status_code == 403, (
        f"{method.upper()} {path} returned {response.status_code} for a "
        "technician. Authentication is not authorization: before this fix every "
        "one of these was reachable by any account that could log in"
    )


def test_the_refusal_names_the_permission_rather_than_the_resource(as_role) -> None:
    """A 403 that says nothing is a 403 nobody can act on."""
    response = as_role("doctor").get("/national/tasks/")
    assert response.status_code == 403
    assert CANONICAL in response.text


def test_a_principal_with_the_permission_is_served(as_role) -> None:
    """POSITIVE. The guard must let the right caller through.

    A negative test alone proves only that something refuses; it cannot tell a
    correct permission check from a router that refuses everyone. This one runs
    against `/intelligence`, the one package in scope that reaches no database
    and no repository at all, so the result is an actual 200 rather than a
    failure further down that would have to be argued about.
    """
    response = as_role("master_admin").get("/intelligence/ai/models")
    assert response.status_code == 200, (
        "master_admin holds `system:admin` and was not served anyway "
        f"({response.status_code}); the router would be refusing everyone, and "
        "the negative tests above would be passing for the wrong reason"
    )


def test_the_task_router_stops_at_the_service_rather_than_at_authorization(as_role) -> None:
    """NR-076, recorded here because this is the test that found it.

    `master_admin` gets *past* authorization on `/national/tasks/` and then
    fails -- not on the unbuilt tables, which is what I expected, but earlier.
    `SQLAlchemyTaskAssignmentRepository` implements `find_by_user` and
    `find_active` while its ABC declares `find_by_assignee`, so the class is
    still abstract and `_get_service()` raises `TypeError` on instantiation.
    Every one of the 29 task endpoints calls `_get_service()` first, so the
    whole router is unreachable for reasons that have nothing to do with this
    fix -- and nothing detected it, because nothing had ever executed it.

    Recorded, not repaired. Making the class instantiable would replace a
    TypeError with a repository whose `save` returns the entity without ever
    touching a session and whose finders return `[]`: silent data loss in place
    of a loud failure. The boundary is fail-closed and stays closed until the
    repositories are real.

    This asserts the boundary actually observed, so repairing NR-076 makes it
    fail and the claim gets restated rather than quietly inherited.
    """
    with pytest.raises(TypeError) as raised:
        as_role("master_admin").get("/national/tasks/")
    assert "SQLAlchemyTaskAssignmentRepository" in str(raised.value)
    assert "find_by_assignee" in str(raised.value)


# ── mass assignment and actor integrity, at the service ──────────────────────

class _Repo:
    """A repository that remembers, which is all these assertions need."""

    def __init__(self) -> None:
        self.saved: list[Any] = []

    def save(self, entity: Any) -> Any:
        self.saved.append(entity)
        return entity

    def get(self, _id: str) -> Any:
        return self.saved[-1] if self.saved else None

    def list(self, **_kw: Any) -> list[Any]:
        return list(self.saved)

    def find_by_execution(self, _id: str) -> list[Any]:
        return []


def _service() -> tuple[TaskEngineService, _Repo, _Repo, _Repo]:
    task_repo, audit_repo, escalation_repo = _Repo(), _Repo(), _Repo()
    service = TaskEngineService(
        task_repo=task_repo,
        queue_repo=_Repo(),
        assignment_repo=_Repo(),
        escalation_repo=escalation_repo,
        sla_repo=_Repo(),
        comment_repo=_Repo(),
        audit_repo=audit_repo,
    )
    task_repo.save(
        NationalTask(id=str(uuid.uuid4()), title="original", created_by="the-creator"),
    )
    return service, task_repo, audit_repo, escalation_repo


@pytest.mark.parametrize(
    "field",
    ["created_by", "assigned_to", "assigned_by", "status", "version", "correlation_id"],
)
def test_update_task_refuses_the_fields_the_caller_does_not_own(field) -> None:
    """NEGATIVE. Each of these was writable from the request body."""
    service, task_repo, _, _ = _service()
    task = task_repo.saved[0]
    with pytest.raises(TaskFieldNotUpdatableError):
        service.update_task(task.id, {field: "attacker"})
    assert task.created_by == "the-creator", "the rejected update wrote anyway"
    assert task.status is TaskStatus.PENDING


def test_update_task_still_updates_what_the_caller_does_own() -> None:
    """POSITIVE. An allowlist that rejects everything is not a fix."""
    service, task_repo, audit_repo, _ = _service()
    task = task_repo.saved[0]
    result = service.update_task(
        task.id, {"title": "renamed", "priority": "high"}, actor_id="99",
    )
    assert result.title == "renamed"
    assert result.priority is TaskPriority.HIGH, (
        "priority was stored as the raw string; `task.priority.value` would "
        "raise on the next read"
    )
    assert audit_repo.saved[-1].actor_id == "99"


def test_the_assignment_actor_is_the_server_s_not_the_body_s() -> None:
    """The route passes `current_user`; the service records what it is given."""
    service, task_repo, audit_repo, _ = _service()
    task = task_repo.saved[0]
    service.assign_task(task.id, assignee_id="target-user", assigned_by="7")
    assert task.assigned_by == "7"
    assert audit_repo.saved[-1].actor_id == "7"


def test_escalation_records_who_escalated_as_well_as_to_whom() -> None:
    """`escalated_by` is a column that existed and was never written.

    `escalated_to` is deliberately still caller-chosen: it names the escalation
    target, which is the caller's decision, not a claim about their identity.
    """
    service, task_repo, _, escalation_repo = _service()
    task = task_repo.saved[0]
    service.escalate_task(task.id, reason="sla", escalated_to="supervisor", escalated_by="7")
    escalation = escalation_repo.saved[-1]
    assert escalation.escalated_by == "7"
    assert escalation.escalated_to == "supervisor"


@pytest.mark.parametrize(
    ("call", "action"),
    [
        (lambda s, t: s.start_task(t.id, "assignee", "7"), "STARTED"),
        (lambda s, t: s.complete_task(t.id, None, "7"), "COMPLETED"),
        (lambda s, t: s.fail_task(t.id, "boom", "7"), "FAILED"),
        (lambda s, t: s.cancel_task(t.id, "reason", "7"), "CANCELLED"),
        (lambda s, t: s.hold_task(t.id, "7"), "ON_HOLD"),
        (lambda s, t: s.resume_task(t.id, "7"), "RESUMED"),
        (lambda s, t: s.delegate_task(t.id, "other", "reason", "7"), "DELEGATED"),
    ],
)
def test_every_transition_records_its_actor(call, action) -> None:
    """`national_task_audit_logs.actor_id` was NULL on every path that wrote it.

    A log that records what happened and not who did it is not an audit trail,
    and the column was there the whole time.
    """
    service, task_repo, audit_repo, _ = _service()
    call(service, task_repo.saved[0])
    entry = audit_repo.saved[-1]
    assert entry.action == action
    assert entry.actor_id == "7", (
        f"the {action} audit row carries actor_id={entry.actor_id!r}"
    )
