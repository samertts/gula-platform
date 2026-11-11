"""The Constitution gate crashed at rule 17 of 25 and nobody noticed. IA-089.

`scripts/constitution_enforcer.py` is the whole of the `Constitution Compliance
(PROGRAM-CONSTITUTION-001)` workflow, which declares `PYTHON_VERSION: "3.14"`.
Rule 17 read

    if isinstance(node, ast.Str) or isinstance(node, ast.Constant):
        val = node.s if isinstance(node, ast.Str) else node.value

`ast.Str` was deprecated in Python 3.8 and REMOVED in 3.14, so on that runner
the line raised

    AttributeError: module 'ast' has no attribute 'Str'

and the process died. Rules 18-25 — security-by-design, circular dependencies,
AI safety, and the four cost-governance articles of PROGRAM-CONSTITUTION-001 —
have never been evaluated there. The job reported `failure`, which looked like
a compliance verdict and was in fact a crash.

The clause was redundant wherever it did work: `ast.Str` only ever matched an
`ast.Constant`, and `node.s` was an alias for `node.value`. Measured on
python3.11, where `ast.Str` still exists: every node `ast.walk` yields for a
string, int or bytes literal reports as `Constant`, and `node.s == node.value`.

WHAT THIS DOES NOT CLAIM. The gate is still red, and that is the correct
result: with rule 17 no longer crashing the enforcer reaches all 25 rules and
reports 9 PASS / 11 WARN / 5 FAIL (score 58.0). Those five are real repo-wide
findings that predate this branch — 1276 duplicate blocks, flake8 E501 at the
79-column default, 3563 unused-symbol heuristics, a `firebase_admin` SDK import
in `shared/notifications/sender.py` that is byte-identical on `origin/main`,
and rule 12, which is derived from the others. The workflow has failed on every
`main` run back to 2026-08-20. Repairing the crash makes the gate able to
answer; it does not make the answer yes.
"""
from __future__ import annotations

import ast
import importlib.util
import pathlib
import re
import sys
import warnings

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
ENFORCER = REPO / "scripts" / "constitution_enforcer.py"
WORKFLOW = REPO / ".github" / "workflows" / "constitution-compliance.yml"

#: Aliases `ast` carried for compatibility and dropped in 3.14. Each one is an
#: AttributeError waiting for the interpreter to move, and none is reachable by
#: `py_compile` or by `flake8 --select=E9,F821` — the gates this repo relies on
#: — because they are attribute lookups inside a function body.
REMOVED_IN_3_14 = ("Str", "Bytes", "Num", "NameConstant", "Ellipsis")

#: Where a crash of this kind takes a CI job down with it.
SCANNED_ROOTS = ("scripts", "backend/app", "shared")


def _load_enforcer():
    spec = importlib.util.spec_from_file_location("_ce_under_test", ENFORCER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_enforcer_imports_at_all():
    """Positive control for every assertion below."""
    enforcer = _load_enforcer()
    assert hasattr(enforcer, "rule17_privacy_by_design")
    assert enforcer.FAIL == "FAIL"


class _AstWithoutRemovedAliases:
    """`ast` as 3.14 presents it: the compatibility aliases simply absent.

    Deleting them from the real module does not work. From 3.12 onward they are
    served by a module-level `__getattr__` deprecation shim rather than living
    in `ast.__dict__`, so `monkeypatch.delattr` removes nothing and the lookup
    succeeds anyway — which is how the first version of this test passed while
    proving nothing. Measured: on python3.13, `"Str" in ast.__dict__` is False
    and `hasattr(ast, "__getattr__")` is True. Substituting the module the
    enforcer looks the name up on is what actually reproduces 3.14.
    """

    def __init__(self, removed):
        self._removed = frozenset(removed)

    def __getattr__(self, name):
        if name in self._removed:
            raise AttributeError(f"module 'ast' has no attribute '{name}'")
        return getattr(ast, name)


def test_the_simulation_really_hides_the_aliases():
    """Positive control for the simulation itself."""
    fake = _AstWithoutRemovedAliases(REMOVED_IN_3_14)
    for name in REMOVED_IN_3_14:
        with pytest.raises(AttributeError, match=name):
            getattr(fake, name)
    # and it is still a usable ast otherwise
    assert fake.parse("x = 1") is not None
    assert fake.Constant is ast.Constant


def test_rule17_survives_an_interpreter_without_the_removed_aliases(
    monkeypatch, tmp_path,
):
    """The behavioural proof, run against a simulated 3.14.

    The CI runner has Python 3.14 and this container does not, so the condition
    is reproduced by giving the enforcer a module on which those names raise.
    The rule must still reach a verdict.
    """
    enforcer = _load_enforcer()
    monkeypatch.setattr(
        enforcer, "ast", _AstWithoutRemovedAliases(REMOVED_IN_3_14),
    )

    # A file whose contents actually drive the walk into the constant branch:
    # one of the rule's own sensitive patterns, as a string literal, with no
    # encrypt/decrypt anywhere — so the rule must look at the constant and
    # then report.
    probe = tmp_path / "probe_privacy.py"
    probe.write_text('FIELD = "national_id"\nCOUNT = 1\nBLOB = b"x"\n')
    monkeypatch.setattr(enforcer, "REPO_ROOT", tmp_path)

    result = enforcer.rule17_privacy_by_design(["probe_privacy.py"])

    assert result["status"] in {enforcer.PASS, enforcer.WARNING, enforcer.FAIL}
    assert result["rule"] == "Rule 17"
    # And the walk really did see the constant, rather than skipping the file:
    assert any("probe_privacy.py" in str(line) for line in result["details"]), (
        f"rule 17 did not inspect the probe file; details={result['details']}"
    )


def test_the_same_rule_sees_a_str_constant_on_this_interpreter_too():
    """Not inert: the branch under repair is the one that finds the match."""
    enforcer = _load_enforcer()
    tree = ast.parse('FIELD = "national_id"\n')
    constants = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    assert "national_id" in constants
    assert enforcer.rule17_privacy_by_design is not None


@pytest.mark.parametrize("alias", REMOVED_IN_3_14)
def test_no_shipped_source_uses_an_ast_alias_removed_in_3_14(alias):
    """Repo-wide ratchet, with the corpus size pinned so it cannot go blind."""
    pattern = re.compile(rf"\bast\.{alias}\b")
    offenders: list[str] = []
    scanned = 0

    for root in SCANNED_ROOTS:
        for path in sorted((REPO / root).rglob("*.py")):
            scanned += 1
            for number, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1,
            ):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    # The repair in constitution_enforcer.py quotes the old
                    # code in a comment on purpose, so the next reader knows
                    # what was there. A comment cannot raise.
                    continue
                if pattern.search(line):
                    offenders.append(f"{path.relative_to(REPO)}:{number}: {stripped}")

    assert scanned > 500, (
        f"positive control: expected to walk the shipped tree, walked {scanned} "
        f"files. If the layout moved, fix the roots rather than the assertion."
    )
    assert not offenders, (
        f"ast.{alias} was removed in Python 3.14 and the Constitution workflow "
        f"runs on 3.14. Use ast.Constant and node.value (IA-089):\n"
        + "\n".join(offenders)
    )


def test_the_scan_covers_the_file_the_crash_was_in():
    """Second positive control: the corpus contains the known-affected file."""
    assert ENFORCER.exists()
    assert ENFORCER.is_relative_to(REPO / "scripts")
    assert "scripts" in SCANNED_ROOTS


def test_the_workflow_still_runs_a_python_without_those_aliases():
    """Ties the ratchet to the fact that makes it necessary.

    If the workflow is ever pinned back below 3.14 the aliases would work
    again — but the project also publishes support for newer interpreters, so
    the ratchet should stay. This asserts the premise rather than silently
    depending on it: a changed version shows up here.
    """
    source = WORKFLOW.read_text()
    match = re.search(r'PYTHON_VERSION:\s*"([^"]+)"', source)
    assert match, "positive control: the workflow declares PYTHON_VERSION"
    major, _, minor = match.group(1).partition(".")
    assert major == "3"
    assert int(minor) >= 14, (
        f"the Constitution workflow now runs Python {match.group(1)}, below the "
        f"3.14 that removed these aliases. The ratchet is still correct — "
        f"nothing here needs relaxing — but IA-089's premise has changed."
    )


def test_this_interpreter_is_not_itself_the_evidence():
    """Honesty check on the simulation above.

    If the container ever moves to 3.14 the monkeypatching becomes a no-op
    rather than a simulation, and the test above would pass for the wrong
    reason. That is fine — it would then be a direct measurement — but say so.
    """
    with warnings.catch_warnings():
        # The lookup itself is what 3.12/3.13 warn about; asking the question
        # must not turn into the finding.
        warnings.simplefilter("ignore", DeprecationWarning)
        simulated = hasattr(ast, "Str")
    assert simulated or sys.version_info >= (3, 14), (
        "ast.Str is absent on an interpreter below 3.14, which should not happen"
    )
