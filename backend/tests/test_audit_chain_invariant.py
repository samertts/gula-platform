"""NR-062 — the audit gap is a ratchet: it may close, it may not widen.

CLAUDE.md states the rule already: "All mutations MUST write to the audit log
(AuditLog model + hash chain)." The architecture behind it is real and needs no
redesign -- `services/audit_service.py` chains each entry as
SHA-256(previous_chain_hash + record), anchors it off-database under an HMAC
(`AUDIT_ANCHOR_KEY`), and can re-verify the chain (`verify_audit_chain`). That
is tamper-evident, not merely logged.

What is not true today is the coverage. Measured across `app/`:

  1222 mutating endpoints (POST/PUT/PATCH/DELETE) in 42 packages
   951 (77%) in packages that call an audit function somewhere
   271 (22%) in packages containing **no audit call at all**

The 271 is a lower bound on the gap and is the number this file holds. "The
package audits somewhere" does not prove a given endpoint audits, so the true
gap is larger; a module-level pass puts the upper bound at 435. Both are proxies,
which is exactly why this test ratchets a measured number rather than asserting
a coverage percentage it cannot actually verify.

The ledger below may shrink. It may never grow. Closing the gap properly is a
design decision recorded in the register, not something to fake here.
"""

from __future__ import annotations

import ast
import collections
import pathlib

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

_MUTATING = {"post", "put", "patch", "delete"}

#: Tokens that mean "this file participates in auditing". Deliberately broad:
#: a false positive here makes the guard weaker but never wrong, whereas a false
#: negative would invent a gap that does not exist.
_AUDIT_TOKENS = (
    "log_action",
    "audit_service",
    "log_access_decision",
    "AuditLog(",
    "record_audit",
    "write_audit",
    "audit_log(",
)

#: Packages that mutate state and contain no audit call anywhere, with the
#: number of mutating endpoints measured at the time of writing.
#: A count may fall. It may not rise, and a new package may not appear.
DECLARED_UNAUDITED_MUTATION_PACKAGES = {
    "app/ai_fabric": 23,
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
        if any(token in source for token in _AUDIT_TOKENS):
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
