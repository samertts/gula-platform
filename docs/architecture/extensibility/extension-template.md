# Extension template

**PROGRAM-EXT-001, Phase 10.** The minimum a new capability or domain ships
with. Copy the layout, fill the manifest, delete nothing.

## 1. Layout

```
app/<area>/<name>/
├── __init__.py            # exports the descriptor, nothing else
├── manifest.py            # the CapabilityDescriptor — the contract
├── contracts.py           # request/response/error models (Pydantic)
├── events.py              # the events this capability publishes
├── service.py             # behaviour; takes a sqlalchemy.orm.Session
├── routes.py              # versioned FastAPI routes, plain `def` handlers
└── README.md              # one page; linked from the manifest

backend/migrations/versions/<date>_<n>_<name>.py   # new revision, never an edit
backend/tests/test_<name>.py                       # against migrated PostgreSQL
```

Six files. If a capability needs more than this to be understood, the extra is
the capability's business, not the platform's.

## 2. `manifest.py`

```python
from app.kernel.types import (
    CapabilityAudit, CapabilityDescriptor, CapabilityMaturity,
    FeatureFlagClass, TenantScope,
)

DESCRIPTOR = CapabilityDescriptor(
    capability_id="cap.<area>.<name>",
    name="<name>",
    version="1.0.0",
    owner="<team>",
    description="<one sentence, for someone who has not read the code>",
    domain="<clinical|infrastructure|identity_security|platform|integration|...>",
    maturity=CapabilityMaturity.EXPERIMENTAL,
    flag_class=FeatureFlagClass.EXPERIMENTAL,
    feature_flag="ENABLE_<NAME>",
    tenant_scope=TenantScope.TENANT,
    dependencies=["audit_logging", "authorization_rbac"],
    required_permissions=["<resource>.<action>"],
    required_context=["tenant_id", "actor_account_id"],
    audit=CapabilityAudit(
        writes_audit=True,
        audit_service="app.identity.services.canonical_audit.CanonicalAuditService",
        data_classification="CLINICAL_SENSITIVE",
        retention_days=3650,
    ),
    module_path="app/<area>/<name>",
    documentation=["app/<area>/<name>/README.md"],
    test_paths=["backend/tests/test_<name>.py"],
)
```

## 3. `service.py` — the four rules

```python
from sqlalchemy.orm import Session          # 1. sync Session; never AsyncSession

class <Name>Service:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)   # 2. one audit writer

    def do_the_thing(self, *, tenant_id: int, actor, payload) -> Result:
        # 3. authorization is a server decision, per request, never a flag
        decision = AuthorizationDecisionService(self.session).authorize(actor, request)
        self.audit.record(...)                        # 4. audit before you act
        if not decision.allowed:
            raise <Name>Denied("permission_denied")
        rows = (
            self.session.query(Thing)
            .filter(Thing.tenant_id == tenant_id)     # every query, every time
            .all()
        )
        return Result(...)
```

Audit is written **before** the decision is acted on, for allow and for deny
alike. That ordering is what makes the trail trustworthy: an audit written only
on success records what worked, not what was attempted.

## 4. `routes.py`

```python
router = APIRouter(prefix="/api/v1/<name>", tags=["<Name>"])

@router.get("")
def list_things(                                    # plain `def` — see below
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
) -> ListResponse:
    return <Name>Service(db).list(actor=actor)
```

Handlers are `def`, not `async def`. The session is synchronous, so an `async`
handler runs blocking database work on the event loop; FastAPI runs a plain
`def` handler in a threadpool, which is where blocking work belongs. NR-044 is
what happened the last time this was got wrong.

## 5. Migration

New revision. Idempotent (`_has_table` / `_has_column` / `_has_index` guards).
New columns nullable or with a `server_default`. Reversible. Never edit an
existing revision — existing databases have already run it.

## 6. Tests

Against migrated PostgreSQL. Not `create_all()`, not SQLite, not a mocked
session — for anything touching patient data, authorization, audit or tenancy.
A mock proves the shape of a call; it cannot prove a predicate.

Minimum: the allow path executes; each denial boundary denies for its own
reason; the tenant filter holds against a second tenant's rows; the audit row
exists and its chain verifies.

## 7. Before opening the PR

Run these locally. On a feature-branch PR the extensibility guards are not
executed by any workflow — see README.md — so local is the only place they run
until the change reaches `main`.

```bash
cd backend
python3 -m pytest tests/test_extensibility_guards.py -q
python3 -m pytest tests/test_<name>.py -q
ruff check app/<area>/<name>
```

## 8. Why there is no generated example

A synthetic business implementation would be a lie in the repository: code that
looks finished, does nothing, and gets copied. `app/capabilities/` already holds
268 files of exactly that, none of which imports (NR-050).

The template is proved instead by
`backend/tests/test_extensibility_guards.py::TestSyntheticExtension`, which
builds a complete descriptor in memory and asserts all ten properties the
platform requires of a real one. It proves the contract without leaving a
plausible-looking corpse in `app/`.
