"""NR-142 — the `services/` tree cannot say who is calling, so it must not act.

WHAT THIS CLOSES
----------------
`services/lab`, `patient`, `order`, `result`, `sample`, `notification`, `ai` and
`autonomous_manager` perform **no authentication and no authorization of any
kind**. The string ``Authorization`` appears in each of them exactly once, in
``CORSMiddleware(allow_headers=[...])``, where it grants a browser permission to
send a header that nothing then reads.

They are not inert. ``docker-compose.full.yml`` — a deployment target CLAUDE.md
documents — builds all eight and points them at ``labdb`` through pgbouncer, the
same database the monolith serves. Their handlers issue raw asyncpg INSERT and
SELECT against ``patients``, ``laboratories`` and ``lab_orders`` with no caller,
no tenant and no audit. NR-143 moved their published ports to loopback, and that
is containment, not a fix: a bound port is a deployment property, and the next
compose file or the next `-p` flag undoes it.

WHY IT FAILS CLOSED RATHER THAN AUTHENTICATING
-----------------------------------------------
This is the same answer `nhop-platform/app/core/trusted_context.py` reached for
NR-127, and it is quoted here because the reasoning is the point:

    "There is no trusted context to derive, and inventing a second identity
     system in this service is not the answer. This module therefore refuses to
     produce a context at all. A service that cannot say who is calling must not
     act on their behalf -- an unavailable endpoint is recoverable, a clinical
     record forged under a real laboratory's name is not."

NIAM is the canonical identity authority for this platform. Building a ninth
and tenth authentication stack inside a tree whose disposition is still open
(ADR-028 classified it DORMANT, which describes maintenance, not safety) would
be inventing exactly the second identity system that answer rejects — and would
have to be torn out again if the tree is retired.

So the perimeter refuses, and it refuses **whole**. That is correct whichever
way the disposition decision goes: if the tree is retired, nothing is lost; if
it is adopted, federating a real token check here is the one place to do it.

WHY A PERIMETER AND NOT FORTY DECORATORS
-----------------------------------------
Roughly forty route decorators across the eight services touch data. Guarding
each one is the shape NR-147 already rejected: the change the next `@app.post`
silently undoes. This is one object, attached once per service, and a new route
is covered the moment it is declared.

It is a middleware rather than a dependency because these services declare their
routes directly on the app (`@app.get(...)`) rather than through a router, so
there is no single router to hang a dependency on, and FastAPI's app-level
`dependencies=[...]` cannot exempt the liveness probe. The monolith already uses
this exact shape in `ReadinessMiddleware`: refuse every path that is not on a
small, explicit allowlist.

NOTHING OUTSIDE THE PROCESS CAN SWITCH IT ON
---------------------------------------------
There is deliberately no environment variable and no header that disables this,
following the same rule NR-127 set: *anything switchable from outside the
process is the defect this module exists to remove.* A test that needs a caller
replaces the middleware in its own app instance.

WHEN FEDERATION LANDS
---------------------
Replace ``_refuse`` with a real NIAM token validation that puts the resolved
caller on ``request.state``. Every route in these services would then still need
its own tenant and authorization checks — this perimeter is authentication's
absence made safe, never a substitute for authorization.
"""

from __future__ import annotations

from collections.abc import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

#: Paths that may be served without a caller. Liveness only: these reveal no
#: patient, laboratory or order data and carry no tenant. `/metrics` is NOT
#: here -- CLAUDE.md Security Invariant #4 requires a bearer token on the
#: monolith's Prometheus surface, and this tree has no way to check one.
DEFAULT_ALLOWLIST: frozenset[str] = frozenset({"/health"})

REFUSAL_CODE = "SERVICE_HAS_NO_CALLER_IDENTITY"

REFUSAL_DETAIL = (
    "This service cannot authenticate the caller, so it refuses to act. "
    "NIAM is the canonical identity authority for this platform and is not "
    "federated here (NR-142). Use the gula-backend monolith, which authenticates "
    "and authorizes every clinical route."
)


class FailClosedMiddleware(BaseHTTPMiddleware):
    """Refuse every request except an explicit liveness allowlist.

    503 rather than 401 or 403 on purpose: 401 would invite a caller to retry
    with a credential this service cannot check, and 403 would assert a denial
    decision no one here is entitled to make. The honest statement is that the
    capability is unavailable.
    """

    def __init__(self, app, allowlist: Iterable[str] | None = None) -> None:
        super().__init__(app)
        self.allowlist = frozenset(allowlist) if allowlist is not None else DEFAULT_ALLOWLIST

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.allowlist:
            return await call_next(request)
        return self._refuse()

    @staticmethod
    def _refuse() -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"code": REFUSAL_CODE, "detail": REFUSAL_DETAIL},
        )
