"""The compliance router must not attest to something it has not measured.

`/compliance/security-report` and `/compliance/system-status` describe
themselves as reports "for government and ISO 27001 auditors". That audience
makes a wrong sentence in them a different kind of defect from a wrong sentence
elsewhere: nobody reading it can check it, and the correct parts lend their
credibility to the incorrect parts.

Three things were wrong, each a different way for a report to stop being true.

**A claim the code contradicted in the same response.** `security_report`
printed `"multi_tenant": "PASS - per-lab data isolation enforced at query
level"` two keys above `failed_logins_24h`, which ran

    SELECT COUNT(*) FROM audit_logs
    WHERE action = 'login_failed' AND created_at >= NOW() - INTERVAL '24 hours'

with no `lab_id`. `audit_logs.lab_id` exists and carries its own index, so the
omission is not a schema limitation. Executed against PostgreSQL 16 with three
lab-1 and five lab-2 failed logins, a lab-1 admin was served **8**.

**A claim that went stale.** `"PASS - 4 roles: master_admin, admin, staff,
technician"`, as a literal, while `ROLE_PERMISSIONS` carries sixteen -- among
them `ministry_admin` and `province_admin`, which are not lab-scoped at all, and
a six-role financial separation-of-duties set. It is now derived, so adding a
role updates the report.

**A true measurement under a false label.** `/compliance/audit-integrity`
verifies the hash chain platform-wide, which is correct and unavoidable:
`_get_last_chain_hash` selects the newest `chain_hash` across all labs, so every
lab's entries interleave in one sequence and a per-lab chain would not verify.
The endpoint then wrote `result["lab_id"] = current_user.lab_id` onto it,
presenting a platform-wide count as the caller's. The verification is unchanged;
the label now says what the number covers.

These tests are read-only. They parse the module rather than serve it, so they
run in the unit gate with no database.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

ROUTES = pathlib.Path(__file__).resolve().parents[1] / "app" / "routes" / "compliance.py"


@pytest.fixture(scope="module")
def module() -> ast.Module:
    return ast.parse(ROUTES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def functions(module) -> dict[str, ast.FunctionDef]:
    return {n.name: n for n in module.body if isinstance(n, ast.FunctionDef)}


def _sql_literals(fn: ast.FunctionDef) -> list[str]:
    """Every string handed to `text(...)` anywhere inside `fn`."""
    found = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name not in ("text", "sql_text") or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            found.append(arg.value)
    return found


#: Statements in these reports that name a control the application cannot
#: observe from inside itself -- nginx's rate limits, the TLS terminator, the
#: reverse proxy's header stripping. They are configuration assertions, true or
#: false depending on a deployment this process cannot see. They are recorded
#: rather than removed, because deleting an auditor's checklist line is a
#: product decision, and pinned so the set cannot quietly grow.
#:
#: Was 23. Twelve were converted under §32-D and the ceiling came down with
#: them, because a ratchet that keeps its old headroom is not a ratchet.
#:
#: What the twelve became. Five name controls that live in nginx or the
#: container runtime -- TLS, rate limits, header hiding, attack-path blocking,
#: no-new-privileges -- and are now `UNOBSERVABLE`, each saying where it would
#: have to be checked. Three are measured against the database or the running
#: middleware stack: the two audit-immutability claims ask pg_trigger for
#: `trg_audit_logs_no_update`/`no_delete`, and the body-limit and
#: security-header claims ask `app.user_middleware` what is actually installed.
#: Two -- `multi_tenant` and `object_level_auth` -- became `ENFORCED_BY_GATE`,
#: naming the CI guard that holds each invariant, because this platform has
#: found four tenant-scope defects in as many days and a blanket PASS from
#: inside a request cannot speak for the whole codebase.
#:
#: The eleven that remain are app-internal and derivable -- a hasher in use, a
#: route registered. Weaker than measured, but not the same species as telling
#: an auditor this process verified nginx.
DECLARED_UNVERIFIABLE_CLAIMS = 11


def test_every_audit_log_read_in_a_served_report_is_tenant_scoped(functions) -> None:
    """The defect that was live, in the endpoint that denied it.

    Scoped means the query names `lab_id`. `audit_summary` scopes differently --
    by `LabUser.id` membership rather than the row's own `lab_id` -- and is
    exempted here because it is ORM, not raw SQL; the inconsistency between the
    two strategies is recorded in the register, not enforced by this test.
    """
    offenders = []
    for name in ("security_report", "system_status", "audit_summary", "system_info"):
        fn = functions.get(name)
        if fn is None:
            continue
        for sql in _sql_literals(fn):
            if "audit_logs" not in sql:
                continue
            if "lab_id" not in sql:
                offenders.append((name, " ".join(sql.split())[:90]))

    assert offenders == [], (
        "a served compliance endpoint reads audit_logs without a lab_id "
        f"constraint: {offenders}. audit_logs.lab_id exists and is indexed, so "
        "there is no schema reason to omit it, and these endpoints print "
        "'per-lab data isolation enforced at query level' in the same response."
    )


def test_the_rbac_claim_is_derived_rather_than_asserted(functions, module) -> None:
    """A literal role list is wrong the moment a role is added, and silently.

    The guard is on the *mechanism*, not the number: asserting "16" here would
    itself be a literal that goes stale. What must hold is that no report states
    a role count the code did not compute.
    """
    source = ROUTES.read_text(encoding="utf-8")
    assert "_rbac_claim" in source, "the derivation helper is gone"

    literal_claims = []
    for fn in functions.values():
        for node in ast.walk(fn):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values, strict=False):
                if not (isinstance(key, ast.Constant) and key.value == "rbac"):
                    continue
                if isinstance(value, ast.Constant):
                    literal_claims.append((fn.name, value.value))

    assert literal_claims == [], (
        f"an 'rbac' verdict is a string literal again: {literal_claims}. "
        "It must be computed from ROLE_PERMISSIONS so that adding a role "
        "updates the report instead of silently falsifying it."
    )


def test_the_chain_result_is_not_labelled_as_the_callers_lab(functions) -> None:
    """The chain is global by construction; saying so is the fix.

    `audit_integrity` may keep `lab_id` -- callers read it -- but it must also
    carry the scope, because the number beside it counts every lab's entries.
    """
    fn = functions["audit_integrity"]
    assigned = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Subscript)
                and getattr(target.value, "id", None) == "result"
                and isinstance(target.slice, ast.Constant)
            ):
                assigned.add(target.slice.value)

    assert "scope" in assigned, (
        "audit_integrity sets result['lab_id'] on a platform-wide chain "
        "verification without recording the scope. A lab admin reading "
        "entries_checked beside their own lab_id will read it as their count."
    )


def test_the_unverifiable_claim_count_does_not_grow(functions) -> None:
    """A ratchet on assertion, not on correctness.

    These sentences name controls that live in nginx, the TLS terminator or the
    deployment -- things this process cannot inspect. Each one is a promise the
    report cannot keep on its own. The count may fall as claims become measured
    or are removed. It may not rise.
    """
    literals = 0
    for name in ("security_report", "system_status"):
        fn = functions.get(name)
        if fn is None:
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Dict):
                continue
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(
                    value.value, str
                ) and value.value.startswith(("PASS", "PARTIAL", "FAIL")):
                    literals += 1

    assert literals <= DECLARED_UNVERIFIABLE_CLAIMS, (
        f"{literals} hard-coded PASS/PARTIAL/FAIL verdicts, against a declared "
        f"ceiling of {DECLARED_UNVERIFIABLE_CLAIMS}. A new one means a control "
        "is being attested rather than measured. Measure it, or justify the "
        "raise here explicitly."
    )
