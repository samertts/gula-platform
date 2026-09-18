"""The platform has to be startable, administrable, and able to list a row.

Three defect classes found while proving a clean deployment can actually be
run, all of them invisible to import-time and syntax gates because every one
of them is valid Python that does the wrong thing at runtime.

NR-111 -- A FRESH DEPLOYMENT COULD NOT BE ADMINISTERED AT ALL.
    ``/login`` refuses any account whose role is in PRIVILEGED_ROLES until it
    has an active MFA device (``app/routes/login.py``), and the only enrolment
    endpoint, ``POST /mfa/totp/setup``, is itself behind ``get_current_user``.
    The bootstrap creates exactly one account, the master admin, and it is
    privileged -- so on a clean database nobody could log in, nobody could
    enrol, and no lab could ever be approved. Observed on a live server:
    ``403 MFA enrollment required for privileged accounts``.
    Fixed by ``scripts/enroll_mfa.py``, an out-of-band enrolment that needs
    database credentials rather than a session. The login gate is untouched --
    enrolling ADDS a factor, it never bypasses one.

NR-112 -- THE DOCUMENTED RECOVERY SCRIPT CRASHED BEFORE IT DID ANYTHING.
    ``scripts/create_master_admin.py`` reads ``os.getenv("DATABASE_URL")``
    and never imported ``os``: ``NameError: name 'os' is not defined``, on
    line 1 of real work. It also swallowed every exception into a bare
    ``sys.exit(1)``, so the operator saw a silent failure and an account that
    did not exist. CI's F821 gate covers ``app/`` and ``migrations/`` only,
    which is why it survived. Seven more undefined names were in ``scripts/``
    behind it, including ``Lab`` in ``generate_demo_data.py`` -- the demo
    generator the README documents raised NameError on every run.

NR-113 -- TWENTY-SIX SQL FILTERS COMPILED TO ``WHERE false``.
    ``db.query(Lab).filter(not Lab.is_active)`` is not a SQL negation. Python
    evaluates ``not`` eagerly, an InstrumentedAttribute is truthy, so the
    argument is the literal ``False`` and the statement compiles to
    ``SELECT labs.id FROM labs WHERE false``. It cannot return a row, ever,
    and it raises nothing. Measured consequences on a live server:

      /admin/labs/pending      returned ``total: 0`` with two labs waiting for
                               approval -- the onboarding queue was empty by
                               construction, so no lab could be approved
                               through the intended workflow.
      PACSService.revoke_share never found the share, so it always returned
                               False: a shared radiology study could not be
                               revoked.
      20 LIMS list endpoints   filtered ``not X.is_deleted`` and so returned
                               zero rows regardless of the data.

    The correct idiom was already in the tree three lines above one of the
    defects (``~HospitalMaster.is_deleted``, app/services/hospital_service.py),
    which is what makes this a typo class rather than a design question.

All three ledgers below are shrink-only. Growing one is the regression.
"""
from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
_REPO = _BACKEND.parent
_SCRIPTS = _REPO / "scripts"

_SQL_FILTER_METHODS = frozenset({"filter", "where", "filter_by", "having"})

# Trees whose SQL is built with the ORM. Empty ledger: no call site anywhere
# in them may pass a Python `not` into a SQL filter.
_ORM_TREES = ("backend/app", "services", "nhop-platform")

# NR-113: every site was repaired, so nothing is declared. A new entry here
# means a `WHERE false` was accepted back into the tree.
DECLARED_CONSTANT_FALSE_FILTERS: frozenset[str] = frozenset()
_CONSTANT_FALSE_CEILING = 0

# NR-112: `scripts/` is operator tooling -- backup, restore, demo data,
# certification, master-admin recovery. It is not on CI's F821 path, so this
# is the gate. Empty ledger.
DECLARED_UNDEFINED_NAMES: frozenset[str] = frozenset()
_UNDEFINED_NAME_CEILING = 0


def _python_files(*relative_roots: str):
    for rel in relative_roots:
        root = _REPO / rel
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            yield path


def _not_into_sql_filter() -> list[str]:
    """Every call that hands a Python ``not`` to a SQL filter, as file:line."""
    found = []
    for path in _python_files(*_ORM_TREES):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name not in _SQL_FILTER_METHODS:
                continue
            for arg in node.args:
                if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.Not):
                    rel = path.relative_to(_REPO).as_posix()
                    found.append(f"{rel}:{node.lineno}: {ast.unparse(arg)}")
    return found


def test_no_sql_filter_is_handed_a_python_not() -> None:
    """NR-113. ``filter(not Model.flag)`` compiles to ``WHERE false``."""
    found = _not_into_sql_filter()
    undeclared = [f for f in found if f.split(":")[0] not in DECLARED_CONSTANT_FALSE_FILTERS]
    assert not undeclared, (
        "these SQL filters compile to WHERE false and can never match a row:\n  "
        + "\n  ".join(undeclared)
        + "\nUse ~Model.flag for a NOT NULL column, or Model.flag.is_(False)."
    )


def test_the_constant_false_ledger_only_shrinks() -> None:
    assert len(DECLARED_CONSTANT_FALSE_FILTERS) <= _CONSTANT_FALSE_CEILING, (
        f"the WHERE-false ledger grew to {len(DECLARED_CONSTANT_FALSE_FILTERS)}; "
        f"the ceiling is {_CONSTANT_FALSE_CEILING}"
    )


def test_the_constant_false_ledger_does_not_rot() -> None:
    """A declared site that no longer exists must leave the ledger."""
    live = {f.split(":")[0] for f in _not_into_sql_filter()}
    stale = sorted(DECLARED_CONSTANT_FALSE_FILTERS - live)
    assert not stale, f"these are declared but no longer present: {stale}"


def _undefined_names_in(target: Path) -> list[str]:
    """F821 over a directory, via whichever checker the environment has.

    A checker that is not installed must not read as a clean result. The
    subprocess form of `-m ruff` exits 1 both for "found problems" and for
    "no module named ruff", so the absence is detected explicitly and the
    guard fails rather than reporting nothing.
    """
    try:
        from pyflakes.api import check
        from pyflakes.reporter import Reporter
    except ImportError:
        pass
    else:
        import io

        out, err = io.StringIO(), io.StringIO()
        reporter = Reporter(out, err)
        for path in sorted(target.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            check(path.read_text(encoding="utf-8", errors="replace"), str(path), reporter)
        return [line for line in out.getvalue().splitlines() if "undefined name" in line]

    ruff = shutil.which("ruff")
    argv = (
        [ruff] if ruff
        else [sys.executable, "-m", "ruff"]
    ) + ["check", "--select=F821", "--output-format=concise", str(target)]
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=_REPO, check=False)  # noqa: S603
    unavailable = (
        proc.returncode not in (0, 1)
        or "No module named" in proc.stderr
        or "not found" in proc.stderr.lower()
    )
    if unavailable:
        pytest.fail(
            "neither pyflakes nor ruff could check for undefined names, so this "
            f"guard could not run (rc={proc.returncode}): {proc.stderr.strip()[:300]}",
        )
    return [line for line in proc.stdout.splitlines() if "F821" in line]


def test_the_undefined_name_checker_actually_reports_something(tmp_path: Path) -> None:
    """Positive control. A checker that finds nothing anywhere is not a gate."""
    (tmp_path / "bad.py").write_text("def f():\n    return not_a_real_name\n")
    found = _undefined_names_in(tmp_path)
    assert found, (
        "the undefined-name checker reported nothing for a file that plainly "
        "uses an unbound name, so a clean result from it means nothing"
    )


def test_operator_tooling_has_no_undefined_names() -> None:
    """NR-112. A NameError in a recovery script surfaces during an incident."""
    found = _undefined_names_in(_SCRIPTS)
    undeclared = [
        line for line in found
        if not any(decl in line for decl in DECLARED_UNDEFINED_NAMES)
    ]
    assert not undeclared, (
        "scripts/ carries undefined names that raise NameError at runtime:\n  "
        + "\n  ".join(undeclared)
    )


def test_the_undefined_name_ledger_only_shrinks() -> None:
    assert len(DECLARED_UNDEFINED_NAMES) <= _UNDEFINED_NAME_CEILING, (
        f"the undefined-name ledger grew to {len(DECLARED_UNDEFINED_NAMES)}; "
        f"the ceiling is {_UNDEFINED_NAME_CEILING}"
    )


def test_the_master_admin_recovery_script_can_reach_the_database() -> None:
    """NR-112 precisely: every name it uses at module scope is bound."""
    source = (_SCRIPTS / "create_master_admin.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    assert "os" in imported, (
        "create_master_admin.py reads os.getenv('DATABASE_URL'); without the "
        "import it dies with NameError before it opens a connection"
    )


def test_the_recovery_script_reports_why_it_failed() -> None:
    """A silent `sys.exit(1)` reads as success and loses the reason."""
    source = (_SCRIPTS / "create_master_admin.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    silent = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        says_something = any(
            isinstance(inner, ast.Call)
            and getattr(inner.func, "id", "") == "print"
            for inner in ast.walk(node)
        )
        if not says_something:
            silent.append(node.lineno)
    assert not silent, (
        f"exception handlers at lines {silent} exit without saying what broke"
    )


def test_an_out_of_band_mfa_enrolment_path_exists() -> None:
    """NR-111. Without this the bootstrapped admin can never authenticate."""
    script = _SCRIPTS / "enroll_mfa.py"
    assert script.exists(), (
        "scripts/enroll_mfa.py is the only way a privileged bootstrapped "
        "account can obtain the second factor /login demands"
    )
    tree = ast.parse(script.read_text(encoding="utf-8"))
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "setup_totp" in calls, (
        "the enrolment script must go through MFAService.setup_totp so that a "
        "device enrolled out of band is the same device /login checks for"
    )
    assert "log_action" in {
        getattr(node.func, "id", "")
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }, "an out-of-band enrolment is a security mutation and belongs in the audit chain"


def test_the_login_gate_still_demands_a_second_factor_for_privileged_roles() -> None:
    """The fix for NR-111 must not have been to delete the requirement."""
    source = (_BACKEND / "app" / "routes" / "login.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    roles: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", "") == "PRIVILEGED_ROLES" for t in node.targets
        ):
            roles = {
                elt.value for elt in ast.walk(node.value)
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            }
    assert {"master_admin", "ministry_admin", "province_admin"} <= roles, (
        f"PRIVILEGED_ROLES lost a role: {sorted(roles)}"
    )
    assert "has_mfa_enabled" in source, (
        "login.py no longer checks that a privileged account has a second factor"
    )
