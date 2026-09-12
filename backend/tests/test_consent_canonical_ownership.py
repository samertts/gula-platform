"""NR-060 — Consent has one canonical owner, and a permissive stand-in must stay unreachable.

Seven ORM classes map seven `*consent*` tables across six domains. None of them
duplicates another's table, so this was never the one-table-two-owners problem
NR-051 solved; it is seven concepts sharing a word. Four are migration-backed,
three are ORM-only, and an eighth consent implementation is not an ORM model at
all -- `citizen_platform.privacy.ConsentEngine` keeps consent in a process-local
dict.

The canonical owner is decided by evidence rather than preference: of the eight,
exactly one is wired into an authorization decision. `security/consent_dep.py`
gates citizen reads (`services/mpi/api.py`) by querying `consents` through
`services/consent_service.py`, and writes an audit row on every outcome --
allow, deny and emergency break-glass alike. The rest are read and written only
by their own endpoints.

These tests hold that, and hold the one thing that would be dangerous if it
changed quietly.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

CANONICAL_TABLE = "consents"
CANONICAL_MODEL = "app.models.consent.Consent"

# Every ORM-mapped consent table, with the migration that builds it or None.
# This ledger may shrink. It may never grow without a stated owner.
DECLARED_CONSENT_TABLES = {
    "consents": "20260417_0001_consent_table.py",
    "niam_consents": "20260814_0006_security_audit_governance.py",
    "niam_lifecycle_consents": "20260723_0002_niam_completion_tables.py",
    "trust_consent_records": "20260716_0013_national_trust_platform_tables.py",
    # ORM-only. All three are already declared in test_schema_fidelity's
    # unbuilt ledger, so they are visible there rather than hidden here.
    "dp_consent_directives": None,
    "national_consents": None,
    "rp_consent_records": None,
}


def _consent_tables_in_orm() -> set[str]:
    """Every `__tablename__` containing 'consent', by AST — no import needed."""
    found: set[str] = set()
    for path in (BACKEND / "app").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)
                        and "consent" in stmt.value.value
                    ):
                        found.add(stmt.value.value)
    return found


def test_the_consent_implementation_ledger_is_accurate() -> None:
    """Guard the guard, and stop an eighth consent table appearing unnamed.

    A new consent table is not forbidden — it has to be declared here with the
    migration that builds it, or with None and an entry in the schema-fidelity
    unbuilt ledger. What it may not do is arrive silently.
    """
    actual = _consent_tables_in_orm()
    assert actual == set(DECLARED_CONSENT_TABLES), (
        "the set of consent tables changed; declare the new owner rather than "
        f"leaving it unnamed. added={sorted(actual - set(DECLARED_CONSENT_TABLES))} "
        f"removed={sorted(set(DECLARED_CONSENT_TABLES) - actual)}"
    )


def test_the_declared_migrations_still_build_their_tables() -> None:
    """A ledger entry that stops being true should fail rather than rot."""
    versions = BACKEND / "migrations" / "versions"
    for table, migration in DECLARED_CONSENT_TABLES.items():
        if migration is None:
            continue
        path = versions / migration
        assert path.is_file(), f"{migration} is gone; {table}'s ledger entry is stale"
        assert table in path.read_text(encoding="utf-8"), (
            f"{migration} no longer creates {table}; re-derive the ledger entry"
        )


def test_the_enforced_consent_path_reads_the_canonical_store() -> None:
    """The decision itself: whichever store authorization consults is canonical.

    `require_consent` is the only consent check wired into a route dependency.
    It must resolve to `consents`, and it must audit the decision — a consent
    gate that allows without leaving evidence is worse than no gate, because it
    looks like one.
    """
    from app.models.consent import Consent
    from app.security import consent_dep

    assert Consent.__tablename__ == CANONICAL_TABLE
    assert f"{Consent.__module__}.{Consent.__name__}" == CANONICAL_MODEL

    source = inspect.getsource(consent_dep)
    assert "consent_service.check_active_consent" in source, (
        "require_consent no longer reads the canonical consent store"
    )
    assert "log_access_decision" in source, (
        "require_consent no longer audits its decision"
    )

    # Five decision branches, each audited: owner bypass, emergency denied
    # (non-doctor), emergency allowed, no-consent deny, consent allow.
    assert source.count("log_access_decision(") >= 5, (
        "a decision branch in require_consent stopped writing an audit row"
    )


async def test_a_permissive_consent_service_is_not_reachable() -> None:
    """The one that would be dangerous if it changed quietly.

    `national/security/consent_enforcement.py::ConsentEnforcementService`
    returns `granted=True` for any input and its `log_consent_check` is `pass`.
    It is unreachable for two independent reasons: `national_router` is not
    registered by `factory.py`, and its only call site passes `citizen_id=` to a
    parameter named `patient_id` while omitting the required `requestor_id`, so
    the call would raise TypeError before returning anything.

    This test does not demand that it be fixed — it may well be an intentional
    delegating stub. It demands that the two facts stay tied together: if the
    service still grants unconditionally, it must remain unreachable. Wiring
    that router up, or "fixing" the call signature, fails here instead of
    quietly turning consent into an unconditional ALLOW.
    """
    import inspect as _inspect

    from app import factory
    from app.national.security.consent_enforcement import ConsentEnforcementService

    service = ConsentEnforcementService()
    denied_by_default = await service.check_consent(
        patient_id="no-such-subject",
        scope="read:nothing",
        requestor_id="no-such-actor",
    )
    if not denied_by_default.granted:
        return  # It fails closed now. Reachability no longer matters.

    # Read the real registration function rather than the built app: this
    # FastAPI version defers route flattening behind `_IncludedRouter`, and
    # `openapi()` can fail for reasons unrelated to consent, which would make
    # this test pass or fail for the wrong reason.
    registration = _inspect.getsource(factory._register_routes)
    assert "national_router" not in registration, (
        "ConsentEnforcementService grants unconditionally for any input and its "
        "log_consent_check is `pass`, and factory._register_routes now registers "
        "the router that exposes it at /national/security/consent/check. Either "
        "make the service fail closed, or do not register that router."
    )


def test_in_memory_citizen_consent_is_not_an_authorization_input() -> None:
    """`ConsentEngine` holds consent in `self._consents`, a process-local dict.

    That is survivable only while nothing authorizes on it: the records vanish
    on restart and are invisible to the other gunicorn workers, so a grant made
    on one worker is absent on the next request. Today its only consumers build
    the citizen dashboard, which misinforms rather than mis-authorizes.

    If an access-control path ever consults it, consent becomes per-process and
    non-durable. That fails here first.
    """
    from app.citizen_platform import privacy

    source = inspect.getsource(privacy)
    assert "self._consents: dict" in source, (
        "ConsentEngine's storage changed; re-derive whether this guard still applies"
    )

    enforcement_modules = [
        BACKEND / "app" / "security" / "consent_dep.py",
        BACKEND / "app" / "services" / "consent_service.py",
        BACKEND / "app" / "services" / "authorization_service.py",
    ]
    for path in enforcement_modules:
        text = path.read_text(encoding="utf-8")
        assert "ConsentEngine" not in text, (
            f"{path.name} consults the in-memory ConsentEngine; consent would "
            "become per-worker and would not survive a restart"
        )
