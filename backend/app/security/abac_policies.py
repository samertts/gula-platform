"""Default ABAC policy set for HTTP route enforcement (Wave B unit B1).

B1 introduces ABAC enforcement on the protected HTTP routes of the NIAM
identity surface. The policy set shipped here is intentionally *permissive at
the resource level*: any authenticated subject may access any protected NIAM
resource. This is the behaviour-preserving baseline — B1 adds the enforcement
and audit *mechanism* without changing who can call what today. Fine-grained
deny policies are layered on top of these rules in later waves; because the
engine is deny-overrides (rules are evaluated in priority-then-id order and
the first matching rule decides), a higher-priority DENY rule always wins.
"""

from __future__ import annotations

from app.security.abac import ABACRule, Effect

# Authoritative registry of the NIAM resource identifiers protected by the
# B1 route-enforcement layer. Kept as a single source of truth so that the
# coverage test and the router wiring can never drift apart.
NIAM_ABAC_RESOURCES: tuple[str, ...] = (
    "niam:persons",
    "niam:accounts",
    "niam:auth",
    "niam:sessions",
    "niam:devices",
    "niam:governance",
    "niam:trust",
    "niam:lifecycle",
    "niam:federation",
    "niam:certificates",
    "niam:workflows",
    "niam:notifications",
    "niam:adaptive-auth",
    "niam:admin",
    "niam:compliance",
    "niam:workspaces",
    "niam:citizens",
    "niam:professional-registry",
    "niam:domains",
)


def niam_path_prefixes() -> tuple[str, ...]:
    """Return the URL path prefixes that map onto NIAM ABAC resources."""
    return tuple(f"/niam/{resource.split(':', 1)[1]}" for resource in NIAM_ABAC_RESOURCES)


def build_default_abac_rules() -> list[ABACRule]:
    """Return the default permissive rule set for the NIAM surface.

    One ALLOW rule per NIAM resource; rules match any action and carry no
    conditions, so every authenticated subject currently passes. Deny rules
    added at higher priority (or with a lower id at equal priority) override
    these defaults.
    """
    rules: list[ABACRule] = []
    for resource in NIAM_ABAC_RESOURCES:
        suffix = resource.split(":", 1)[1].replace("-", "_")
        rules.append(
            ABACRule(
                id=f"abac.niam.{suffix}.allow",
                name=f"Allow authenticated subject on {resource}",
                description=(
                    f"B1 default policy: any authenticated subject may perform "
                    f"any action on the {resource} surface. Fine-grained deny "
                    f"policies are layered on top via deny-overrides."
                ),
                effect=Effect.ALLOW,
                resource=resource,
                action="*",
                priority=100,
            )
        )
    return rules
