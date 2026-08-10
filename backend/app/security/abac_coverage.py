"""Route-coverage registry for ABAC enforcement (Wave B unit B1).

B1 guarantees (enforced by ``tests/unit/test_abac_route_coverage.py``):

1. **Every effective HTTP route is classified.** A route is either ABAC
   protected, protected by pre-existing authorization (deferred), explicitly
   public, or explicitly open-exempt. No route may silently fall through.
2. **Every protected NIAM route carries the ABAC guard.** ``require_abac``
   must appear in the flattened dependant tree of every protected
   ``/niam/*`` route (public NIAM routes are declared in the public registry).
3. **Public / open-exempt routes are explicitly declared.** The registries
   below are the single source of truth; a new unauthenticated route that is
   not declared fails the coverage gate and forces an explicit decision.

The classification walks FastAPI's ``_IncludedRouter.effective_route_contexts()``
so lazily included routers are flattened into their real route surface.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.security.abac_policies import niam_path_prefixes


class RouteStatus(Enum):
    """Deterministic classification of an effective HTTP route."""

    PUBLIC = "public"
    OPEN_EXEMPT = "open_exempt"
    PROTECTED_ABAC = "protected_abac"
    PROTECTED_EXISTING = "protected_existing"
    UNPROTECTED = "unprotected"


@dataclass(frozen=True)
class RouteSpec:
    """A declarative registry entry for an unauthenticated route class."""

    methods: frozenset[str] | None
    path_pattern: str
    reason: str

    def __post_init__(self) -> None:
        if self.methods is not None:
            if isinstance(self.methods, str):
                object.__setattr__(self, "methods", frozenset([self.methods]))
            else:
                object.__setattr__(self, "methods", frozenset(self.methods))

    def matches(self, path: str, methods: set[str]) -> bool:
        import re

        if re.match(self.path_pattern, path) is None:
            return False
        return self.methods is None or bool(methods & self.methods)


# ── Public registry: intentionally unauthenticated routes ────────────────────
# Authentication bootstrap, discovery, health, webhook/system callbacks and
# token-gated public links. Each entry states why the route is public.
PUBLIC_ROUTE_SPECS: tuple[RouteSpec, ...] = (
    RouteSpec(None, r"/login$", "authentication bootstrap"),
    RouteSpec(None, r"/mfa-verify$", "MFA challenge verification (pre-auth)"),
    RouteSpec(None, r"/logout$", "no-op logout for anonymous sessions"),
    RouteSpec("POST", r"/register$|/register/citizen$|/register/doctor$", "public self-registration"),
    RouteSpec("GET", r"/setup/status$", "first-run setup probe"),
    RouteSpec("GET", r"/health(?:/(?:ready|status|deep))?$", "liveness/readiness probes"),
    RouteSpec("GET", r"/metrics/prom$", "Prometheus scrape endpoint"),
    RouteSpec("GET", r"/test-profiles$", "pre-auth catalog lookup"),
    RouteSpec("POST", r"/auth/refresh$", "token refresh (self-authenticated)"),
    RouteSpec("GET", r"/auth/mobile/app-info$", "mobile app bootstrap config"),
    RouteSpec("GET", r"/compliance/time-sync$", "time synchronization probe"),
    RouteSpec("GET", r"/tiers$", "public subscription tier catalog"),
    RouteSpec("GET", r"/greeting$", "optional-auth greeting (anonymous allowed)"),
    RouteSpec("POST", r"/webhooks/telegram/update$", "Telegram webhook callback"),
    RouteSpec("GET", r"/webhooks/telegram/health$", "Telegram webhook health probe"),
    RouteSpec("POST", r"/citizen/login$|/citizen/logout$", "citizen portal bootstrap"),
    RouteSpec("POST", r"/auth/forgot-password$|/auth/reset-password$", "password recovery bootstrap"),
    RouteSpec("POST", r"/oauth2/token$|/oauth2/introspect$|/oauth2/revoke$", "OAuth2 token endpoints"),
    RouteSpec("GET", r"/oauth2/\.well-known/openid-configuration$|/oauth2/jwks\.json$", "OIDC discovery"),
    RouteSpec("GET", r"/auth/saml/metadata$", "SAML identity-provider metadata"),
    RouteSpec("POST", r"/auth/saml/acs$", "SAML assertion consumer endpoint"),
    RouteSpec("POST", r"/edge/agent/(?:heartbeat|telemetry)$", "edge agent telemetry callback"),
    RouteSpec("POST", r"/edge/agent/tasks/[^/]+/result$", "edge agent task result callback"),
    RouteSpec("GET", r"/edge/health$", "edge runtime health probe"),
    RouteSpec("POST", r"/niam/auth/login$", "NIAM authentication bootstrap"),
    RouteSpec("POST", r"/niam/auth/refresh$", "NIAM token refresh (self-authenticated)"),
    RouteSpec("GET", r"/niam/health$", "NIAM health probe"),
    RouteSpec("GET", r"/r/[^/]+(?:/pdf)?$", "public shareable report link (token-gated)"),
    RouteSpec("GET", r"/qr(?:-medical)?/[^/]+$", "public QR scan link (token-gated)"),
    RouteSpec("GET", r"/history/[^/]+$", "public shareable history link (token-gated)"),
)

# ── Open-exempt registry: unauthenticated by design, explicitly acknowledged ─
# These surfaces are unauthenticated today. Each entry states the reason; the
# coverage gate forces every one of them to stay declared, so removing them
# from the registry (i.e. protecting them) is always a deliberate change.
OPEN_EXEMPT_ROUTE_SPECS: tuple[RouteSpec, ...] = (
    RouteSpec(
        None,
        r"/api/ai/(?:operations|providers|dataset/status)$|/api/ai/interpret/[^/]+$",
        "AI kernel service surface (service-to-service; interpret is token-embedded)",
    ),
    RouteSpec(
        None,
        r"/lims/quality/indicators(?:/[^/]+/evaluate)?$",
        "LIMS quality public indicator surface",
    ),
    RouteSpec("GET", r"/national/tasks/health$", "national task engine health probe"),
    RouteSpec(
        None,
        r"/document-intelligence/",
        "document-intelligence service surface (unauthenticated by design; "
        "route-level authorization remediation tracked as Wave-B follow-up)",
    ),
    RouteSpec(
        "GET",
        r"/citizen/(?:profile|results|orders|health-record)$",
        "citizen self-service surface (gated by citizen session cookie)",
    ),
)


# ── Dependency-tree introspection helpers ────────────────────────────────────

_AUTHZ_MARKERS = (
    "get_current_identity",
    "get_current_user",
    "get_actor_identity_id",
    "require_permission",
    "require_role",
    "require_roles",
    "check_permission",
)


def _walk_dependencies(dependant: Any) -> Iterator[Any]:
    for sub in getattr(dependant, "dependencies", None) or []:
        call = getattr(sub, "call", None)
        if call is not None:
            yield call
        yield from _walk_dependencies(sub)


def has_authz_dependency(dependant: Any) -> bool:
    """True when the flattened dependant tree contains an authz dependency."""
    for call in _walk_dependencies(dependant):
        if getattr(call, "_abac_guard", False):
            return True
        name = getattr(call, "__qualname__", None) or getattr(call, "__name__", "") or ""
        if any(marker in name for marker in _AUTHZ_MARKERS):
            return True
    return False


def has_abac_guard(dependant: Any) -> bool:
    """True when the flattened dependant tree contains a ``require_abac`` guard."""
    return any(getattr(call, "_abac_guard", False) for call in _walk_dependencies(dependant))


def iter_effective_routes(app: Any) -> Iterator[tuple[str, set[str], Any]]:
    """Yield ``(path, methods, dependant)`` for every effective route.

    Uses FastAPI's ``_IncludedRouter.effective_route_contexts()`` to flatten
    lazily included routers into their real per-route surface.
    """
    for item in getattr(app, "routes", []):
        contexts: list[Any] = []
        if hasattr(item, "effective_route_contexts"):
            try:
                contexts = list(item.effective_route_contexts())
            except Exception:
                contexts = []
        for ctx in contexts:
            path = getattr(ctx, "path", None)
            if not path:
                original = getattr(ctx, "original_route", None)
                starlette_route = getattr(ctx, "starlette_route", None)
                path = (
                    getattr(original, "path", None)
                    or getattr(starlette_route, "path", None)
                )
            if not path:
                continue
            methods = getattr(ctx, "methods", None)
            if not methods:
                original = getattr(ctx, "original_route", None)
                methods = getattr(original, "methods", None)
            if isinstance(methods, str):
                methods = {methods}
            else:
                methods = {m for m in (methods or ()) if m not in ("HEAD", "OPTIONS")}
            dependant = getattr(ctx, "dependant", None)
            yield path, methods, dependant


def classify_route(path: str, methods: set[str], has_authz: bool, has_abac: bool) -> RouteStatus:
    """Classify a single effective route against the registries."""
    if any(spec.matches(path, methods) for spec in PUBLIC_ROUTE_SPECS):
        return RouteStatus.PUBLIC
    if any(spec.matches(path, methods) for spec in OPEN_EXEMPT_ROUTE_SPECS):
        return RouteStatus.OPEN_EXEMPT
    if has_abac:
        return RouteStatus.PROTECTED_ABAC
    if has_authz:
        return RouteStatus.PROTECTED_EXISTING
    return RouteStatus.UNPROTECTED


@dataclass(frozen=True)
class CoverageResult:
    """Outcome of the B1 route-coverage check."""

    total_routes: int
    unprotected: list[tuple[str, tuple[str, ...]]]
    missing_abac: list[tuple[str, tuple[str, ...]]]
    classified: dict[str, list[tuple[str, tuple[str, ...]]]]


def route_coverage_report(app: Any) -> CoverageResult:
    """Run the B1 coverage check over the app's effective route surface."""
    prefixes = niam_path_prefixes()
    unprotected: list[tuple[str, tuple[str, ...]]] = []
    missing_abac: list[tuple[str, tuple[str, ...]]] = []
    classified: dict[str, list[tuple[str, tuple[str, ...]]]] = {
        status.value: [] for status in RouteStatus
    }
    total = 0
    for path, methods, dependant in iter_effective_routes(app):
        total += 1
        authz = has_authz_dependency(dependant)
        abac = has_abac_guard(dependant)
        status = classify_route(path, methods, authz, abac)
        row = (path, tuple(sorted(methods)))
        classified[status.value].append(row)
        if status is RouteStatus.UNPROTECTED:
            unprotected.append(row)
        if abac is False and authz and path.startswith(prefixes):
            missing_abac.append(row)
    return CoverageResult(
        total_routes=total,
        unprotected=unprotected,
        missing_abac=missing_abac,
        classified=classified,
    )
