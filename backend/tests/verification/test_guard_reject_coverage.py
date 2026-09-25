"""Every guarded clinical command should be able to record its own refusal.

Static, database-free, so it runs in every lane.

``ClinicalCommandGuard`` gives a handler three moves: ``claim`` a durable
idempotency receipt, ``complete`` it with an audit event, or ``reject`` it with an
audit event naming the reason. A handler that claims and completes but never
rejects has no way to record *why* a clinical command was refused — and the guard's
audit-failure fallback cannot fire either, because the code that would call it does
not exist.

Measured on 2026-09-25 over all 36 guarded commands: six lack a ``reject`` call in
the handler, and all six are blood bank. This is a ratchet on that number, not a
zero-tolerance rule: the six are pre-existing and closing them changes clinical
response codes, which is the owner's call (NR-033). What the ratchet refuses is a
*seventh*.
"""

from __future__ import annotations

import ast
import pathlib

BACKEND = pathlib.Path(__file__).resolve().parents[2]

GUARDED_ROUTE_MODULES = [
    "app/blood_bank/api/routes.py",
    "app/critical_care/api/routes.py",
    "app/lims/routes.py",
    "app/radiology/routes.py",
    "app/pharmacy/routes.py",
    "app/ems/api/routes.py",
    "app/routes/hospital.py",
]

# NR-033. Pinned exactly, so a repair fails here as loudly as a regression and the
# baseline has to be emptied deliberately.
KNOWN_WITHOUT_REJECT = {
    "blood.reservation.create",
    "blood.reservation.release",
    "blood.sample.create",
    "blood.reaction.create",
    "blood.return.create",
    "blood.discard.create",
}


def _calls(node: ast.AST, attr: str) -> list[ast.Call]:
    return [
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == attr
    ]


def _operation(call: ast.Call) -> str:
    for kw in call.keywords:
        if kw.arg == "operation" and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return "<dynamic>"


def _census() -> tuple[set[str], set[str]]:
    """Return (every guarded operation, those whose handler never calls reject).

    Operations built at runtime are reported as ``<dynamic>`` and excluded from the
    "missing" set — a dispatcher that takes the operation as a parameter cannot be
    judged by name here, and all four such dispatchers do call ``reject``.
    """
    guarded: set[str] = set()
    missing: set[str] = set()
    for rel in GUARDED_ROUTE_MODULES:
        path = BACKEND / rel
        assert path.exists(), f"{rel} moved; update GUARDED_ROUTE_MODULES"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            claims = _calls(fn, "claim")
            if not claims:
                continue
            rejects = _calls(fn, "reject")
            for claim in claims:
                op = _operation(claim)
                guarded.add(op)
                if not rejects and op != "<dynamic>":
                    missing.add(op)
    return guarded, missing


def test_no_new_guarded_command_lacks_a_rejection_path() -> None:
    """A seventh command with no way to record a refusal is a regression."""
    _guarded, missing = _census()
    unexpected = missing - KNOWN_WITHOUT_REJECT
    assert unexpected == set(), (
        "these guarded clinical commands cannot record why they refused, so a failed "
        f"attempt leaves no reason in the audit trail: {sorted(unexpected)}"
    )


def test_the_recorded_gap_is_still_exactly_the_six_blood_bank_commands() -> None:
    """Pin NR-033 both ways.

    When a rejection path is added this fails, and the baseline must be emptied
    deliberately — which is the moment to re-run the failure-trace evidence rather
    than inherit it.
    """
    _guarded, missing = _census()
    assert missing == KNOWN_WITHOUT_REJECT, (
        f"the gap changed: now {sorted(missing)}, recorded {sorted(KNOWN_WITHOUT_REJECT)}"
    )


def test_the_census_actually_found_the_guarded_surface() -> None:
    """Positive control: a census that found nothing would pass both tests above.

    A sweep over an empty list passes vacuously, so the size of the surface is
    asserted rather than assumed.
    """
    guarded, _missing = _census()
    assert len(guarded) >= 25, (
        f"only {len(guarded)} guarded operations found; the census is not reaching the "
        "route modules and the ratchets above prove nothing"
    )
