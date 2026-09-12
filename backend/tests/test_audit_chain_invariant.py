"""NR-062 — the audit gap is a ratchet: it may close, it may not widen.

CLAUDE.md states the rule already: "All mutations MUST write to the audit log
(AuditLog model + hash chain)." The architecture behind it is real and needs no
redesign -- `services/audit_service.py` chains each entry as
SHA-256(previous_chain_hash + record), anchors it off-database under an HMAC
(`AUDIT_ANCHOR_KEY`), and can re-verify the chain (`verify_audit_chain`). That
is tamper-evident, not merely logged.

What is not true today is the coverage. Measured across `app/`:

  1222 mutating endpoints (POST/PUT/PATCH/DELETE) in 42 packages
   894 (73%) in packages that call an audit function somewhere
   328 (27%) in 27 packages containing **no audit call at all**

The 328 corrects this file's own first measurement of 271 across 25 packages.
Nothing regressed: the detector did. It matched its tokens as plain substrings,
so `query_audit_log(` and `_write_audit` counted as auditing (see _AUDIT_TOKENS
below). Word-boundary matching restores app/control_plane (10 endpoints) and
app/governance (47) to the ledger. Every other declared count was and remains
exact.

The 328 is still a **lower bound**: "the package audits somewhere" does not
prove a given endpoint audits. Measured per module rather than per package,
**130 of the 160 modules containing a mutating endpoint contain no audit call,
covering 1065 of the 1222 endpoints** -- the upper bound. Both are proxies,
which is exactly why this file ratchets measured numbers rather than asserting
a coverage percentage it cannot verify.

The ledger below may shrink. It may never grow. Closing the gap properly is a
design decision recorded in the register, not something to fake here.
"""

from __future__ import annotations

import ast
import collections
import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

_MUTATING = {"post", "put", "patch", "delete"}

#: Tokens that mean "this file participates in auditing", matched on a word
#: boundary.
#:
#: The first version of this file matched them as plain substrings, reasoning
#: that a false positive makes the guard weaker but never wrong. That reasoning
#: was incomplete: a false positive here does not weaken the guard evenly, it
#: silently removes a whole package from the ledger. Two packages were removed
#: that way, and neither audits:
#:
#:   app/control_plane  `audit_log(` matched `query_audit_log(`,
#:                      `access_audit_log(` and `get_audit_log(` -- three
#:                      helpers that *read* an audit log.
#:   app/governance     `write_audit` matched `_write_audit`, a repository
#:                      method that writes a `HealthNumberAudit` row with
#:                      `changed_by="system"` for every create, update and
#:                      delete on every governance entity (NR-066). Not the
#:                      canonical chain, and not the real actor.
#:
#: 47 of app/governance's mutating endpoints were hidden by that one underscore
#: -- the second-largest gap in the repository after payments.
_AUDIT_TOKENS = (
    r"\blog_action\b",
    r"\baudit_service\b",
    r"\blog_access_decision\b",
    r"\bAuditLog\(",
    r"\brecord_audit\b",
    r"\bwrite_audit\b",
    r"\baudit_log\(",
)

#: Packages that mutate state and contain no audit call anywhere, with the
#: number of mutating endpoints measured at the time of writing.
#: A count may fall. It may not rise, and a new package may not appear.
DECLARED_UNAUDITED_MUTATION_PACKAGES = {
    "app/ai_fabric": 23,
    "app/control_plane": 10,
    "app/billing": 5,
    "app/biomedical": 11,
    "app/blood_bank": 21,
    "app/capabilities": 29,
    "app/chronic_care": 6,
    "app/command_center": 6,
    "app/command_intelligence": 2,
    "app/contracts": 1,
    "app/critical_care": 14,
    "app/devices": 15,
    "app/document_intelligence": 25,
    "app/governance": 47,
    "app/health_data": 3,
    "app/integration": 9,
    "app/knowledge_graph": 6,
    "app/lifecycle_platform": 7,
    "app/notifications": 1,
    "app/payments": 34,
    "app/pilot_platform": 6,
    "app/public_health": 8,
    "app/reference": 3,
    "app/research_platform": 16,
    "app/roadmap": 11,
    "app/simulation": 3,
    "app/trust": 6,
}


def _measure() -> tuple[dict[str, int], set[str]]:
    """Mutating endpoints per package, and which packages audit anywhere."""
    mutations: collections.Counter[str] = collections.Counter()
    audits: set[str] = set()
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        package = "/".join(path.relative_to(BACKEND).parts[:2])
        if any(re.search(token, source) for token in _AUDIT_TOKENS):
            audits.add(package)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                target = decorator.func if isinstance(decorator, ast.Call) else decorator
                if getattr(target, "attr", None) in _MUTATING:
                    mutations[package] += 1
    return dict(mutations), audits


def test_the_scan_still_finds_the_mutation_surface() -> None:
    """Guard the guard: a scan that finds nothing would ratchet nothing."""
    mutations, _ = _measure()
    total = sum(mutations.values())
    assert total >= 1000, (
        f"only {total} mutating endpoints found across {len(mutations)} packages; "
        "the scan has drifted from the route surface"
    )


def test_the_canonical_audit_chain_is_intact() -> None:
    """The invariant is worth enforcing only because the chain is real.

    If the chain or its off-database anchor were removed, `log_action` would
    still be called everywhere and would still prove nothing.
    """
    source = (APP / "services" / "audit_service.py").read_text(encoding="utf-8")
    for required, why in (
        ("_compute_chain_hash", "per-entry chain hash"),
        ("_get_last_chain_hash", "link to the previous entry"),
        ("sha256", "the hash itself"),
        ("_anchor_hmac", "HMAC over the off-database anchor"),
        ("verify_audit_chain", "the ability to re-verify the chain"),
    ):
        assert required in source, f"the audit chain lost its {why} ({required})"


def test_no_package_starts_mutating_without_auditing() -> None:
    """A new unaudited package is a new blind spot, and fails here."""
    mutations, audits = _measure()
    current = {p: n for p, n in mutations.items() if p not in audits}
    appeared = sorted(set(current) - set(DECLARED_UNAUDITED_MUTATION_PACKAGES))
    assert appeared == [], (
        "these packages now mutate state and contain no audit call anywhere. "
        "CLAUDE.md requires every mutation to reach the hash-chained audit log: "
        f"{appeared}"
    )


def test_the_audit_gap_does_not_widen() -> None:
    """The ratchet.

    Each declared package may shed unaudited mutations; none may gain them.
    Reported per package so a failure names what to fix rather than a total.
    """
    mutations, audits = _measure()
    current = {p: n for p, n in mutations.items() if p not in audits}
    widened = {
        p: (declared, current[p])
        for p, declared in DECLARED_UNAUDITED_MUTATION_PACKAGES.items()
        if current.get(p, 0) > declared
    }
    assert widened == {}, (
        "unaudited mutating endpoints were added to these packages "
        f"(declared -> now): {widened}"
    )


def test_the_ledger_does_not_rot() -> None:
    """An entry that has been fixed should be deleted, not left behind.

    Without this, a package that starts auditing would keep its slot and quietly
    re-acquire unaudited mutations under a stale allowance.
    """
    mutations, audits = _measure()
    current = {p: n for p, n in mutations.items() if p not in audits}
    resolved = sorted(
        p for p in DECLARED_UNAUDITED_MUTATION_PACKAGES if p not in current
    )
    assert resolved == [], (
        "these packages now audit, or no longer mutate; remove them from the "
        f"ledger so the ratchet keeps its grip: {resolved}"
    )


# ---------------------------------------------------------------------------
# Stage 1, second half: measure at module granularity as well as package.
#
# A package ratchet has a blind spot it cannot close: once any module in a
# package audits, the whole package leaves the ledger, and every other module in
# it can acquire unaudited mutations freely. app/national is the live example --
# national/api/routes/interop.py calls log_action, so the package counts as
# auditing while task_engine and workflow_runtime contain no audit call at all
# (NR-065).
#
# So the same measurement is taken per module and ratcheted as two aggregates.
# Two numbers, not a 130-entry list: they catch net widening, which is the
# failure mode worth catching cheaply. What they do NOT catch is a swap -- one
# module fixed and another broken in the same commit. The per-package ledger
# above catches that whenever it crosses a package boundary; within one package
# it would pass, and that limit is stated rather than papered over.
# ---------------------------------------------------------------------------

#: Modules containing a mutating endpoint and no audit call, and the endpoints
#: they carry. Both may fall. Neither may rise.
DECLARED_UNAUDITED_MUTATION_MODULES = 130
DECLARED_UNAUDITED_MODULE_ENDPOINTS = 1065


def _measure_modules() -> tuple[int, int]:
    """(modules that mutate without auditing, endpoints they carry)."""
    modules: collections.Counter[str] = collections.Counter()
    audits: set[str] = set()
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        module = str(path)
        if any(re.search(token, source) for token in _AUDIT_TOKENS):
            audits.add(module)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                target = decorator.func if isinstance(decorator, ast.Call) else decorator
                if getattr(target, "attr", None) in _MUTATING:
                    modules[module] += 1
    unaudited = {m: n for m, n in modules.items() if m not in audits}
    return len(unaudited), sum(unaudited.values())


def test_the_module_level_gap_does_not_widen() -> None:
    """The upper bound, ratcheted alongside the lower one."""
    modules, endpoints = _measure_modules()
    assert modules <= DECLARED_UNAUDITED_MUTATION_MODULES, (
        f"{modules} modules now mutate without auditing, up from "
        f"{DECLARED_UNAUDITED_MUTATION_MODULES}"
    )
    assert endpoints <= DECLARED_UNAUDITED_MODULE_ENDPOINTS, (
        f"{endpoints} mutating endpoints now sit in modules with no audit call, "
        f"up from {DECLARED_UNAUDITED_MODULE_ENDPOINTS}"
    )


def test_the_module_measurement_is_stricter_than_the_package_one() -> None:
    """Guard the guard, and keep the two bounds honestly ordered.

    The module count must exceed the package count, because every endpoint the
    package measure calls unaudited is also unaudited by module. If it ever
    stopped being the larger number, one of the two measurements would be
    reporting something other than what its name says.
    """
    _, module_endpoints = _measure_modules()
    mutations, audits = _measure()
    package_endpoints = sum(
        n for p, n in mutations.items() if p not in audits
    )
    assert module_endpoints > package_endpoints, (
        f"the module-level gap ({module_endpoints}) is no longer larger than "
        f"the package-level gap ({package_endpoints}); one measure has drifted"
    )
