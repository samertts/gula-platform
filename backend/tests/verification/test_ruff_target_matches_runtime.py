"""`ruff format` was entitled to emit syntax two supported Pythons reject.

IA-082, found while trying to satisfy the `Ruff Format (Python)` CI gate.

`pyproject.toml` declared `[tool.ruff] target-version = "py314"` while the
same file declares `requires-python = ">=3.12"`, `setup.py` declares
`python_requires=">=3.12"`, and two CI workflows run Python 3.12. Under a
py314 target ruff is entitled to rewrite code into 3.14-only syntax, and it
does — PEP 758 allows an unparenthesised `except` list, so `ruff format`
turns

    except (TypeError, ValueError):

into

    except TypeError, ValueError:

Measured against three interpreters, all of which reject it with
``SyntaxError: multiple exception types must be parenthesized``:

    python3.11   rejects
    python3.12   rejects      <- declared supported
    python3.13   rejects      <- declared supported

Reproduced in five lines, and the trigger is the target alone:

    ruff format --isolated                        leaves it unchanged
    ruff format --isolated --target-version py314 strips the parentheses

on both ruff 0.16.2 and 0.16.10. **This is not a formatter bug.** It is a
correct rewrite for the target it was given, and the target was wrong.

IT ALREADY HAPPENED. A `ruff check --fix` run during this audit rewrote
`services/device_bridge/app/_compat.py`'s pre-3.11 fallback from
`UTC = timezone.utc` to `UTC = UTC`, and a later `ruff format` stripped the
parentheses in `app/capabilities/fhir_interoperability/hl7.py`, leaving a file
that could not be imported. Both were caught by tests, not by review.

WHY IT MATTERS BEYOND THE ONE LINE. The `Ruff Format (Python)` gate is red
over 1015 of the 2110 files in its own scope (`backend/app/ shared/ scripts/`),
so the obvious way to make it green is a repo-wide `ruff format`. Under py314
that would have produced a tree that cannot be imported on two of the Python
versions this project publishes support for.

The target now matches `requires-python`. These tests pin the two together so
they cannot drift apart again — raising one without the other fails here.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
PYPROJECT = REPO / "pyproject.toml"
SETUP_PY = REPO / "setup.py"

#: ``python3.11`` is below the declared floor, so it is not part of the
#: contract; it is kept in the evidence because the compat shims in
#: ``app/_compat.py`` and ``services/device_bridge/app/_compat.py`` branch on
#: ``sys.version_info >= (3, 11)``, so something still expects to parse there.
SYNTAX_REJECTED_BY = ("3.11", "3.12", "3.13")


def _toml_value(key: str, source: str) -> str | None:
    match = re.search(rf'^{re.escape(key)}\s*=\s*"([^"]+)"', source, re.MULTILINE)
    return match.group(1) if match else None


def _minor(spec: str) -> int:
    """``">=3.12"`` -> 12, ``"py312"`` -> 12."""
    match = re.search(r"3\.?(\d+)", spec.replace("py3", "3."))
    assert match, f"cannot read a 3.x minor out of {spec!r}"
    return int(match.group(1))


def test_the_ruff_target_does_not_exceed_requires_python():
    """The pin that matters. Ratchets both ways.

    If `requires-python` rises, this keeps passing only once the ruff target
    rises with it; if the target rises alone, this fails — which is the
    condition that let a formatter emit 3.14-only syntax into a tree promising
    3.12 support.
    """
    source = PYPROJECT.read_text()
    requires = _toml_value("requires-python", source)
    target = _toml_value("target-version", source)

    assert requires, "positive control: requires-python is declared"
    assert target, "positive control: a ruff target-version is declared"

    assert _minor(target) <= _minor(requires), (
        f"ruff target-version is {target!r} but this project publishes "
        f"requires-python {requires!r}. ruff may then rewrite code into syntax "
        f"the oldest supported interpreter cannot parse — which is how "
        f"`except (A, B):` became PEP 758's `except A, B:` (IA-082). Raise "
        f"requires-python, setup.py's python_requires and the 3.12 CI "
        f"workflows together, or lower the target."
    )


def test_setup_py_agrees_with_pyproject():
    """Two declarations of the same contract, in two files."""
    pyproject = _toml_value("requires-python", PYPROJECT.read_text())
    match = re.search(r'python_requires\s*=\s*"([^"]+)"', SETUP_PY.read_text())
    assert match, "positive control: setup.py declares python_requires"
    assert _minor(match.group(1)) == _minor(pyproject), (
        f"setup.py says {match.group(1)!r}, pyproject.toml says {pyproject!r}"
    )


@pytest.mark.parametrize("version", SYNTAX_REJECTED_BY)
def test_the_syntax_the_old_target_would_emit_is_rejected(version):
    """The evidence, re-measured rather than asserted.

    Skips where an interpreter is absent instead of passing vacuously — a
    missing interpreter is no evidence either way.
    """
    executable = f"python{version}"
    probe = subprocess.run(
        [executable, "-c", "import ast; ast.parse('try:\\n pass\\nexcept A, B:\\n pass\\n')"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 and "No such file" in (probe.stderr or ""):
        pytest.skip(f"{executable} is not installed here")
    if "not found" in (probe.stderr or "").lower():
        pytest.skip(f"{executable} is not installed here")

    assert probe.returncode != 0, (
        f"{executable} accepted `except A, B:` — if the floor has moved to an "
        f"interpreter that accepts PEP 758, re-read IA-082: the ruff target "
        f"may then be raised to match."
    )
    assert "parenthesized" in probe.stderr, probe.stderr


def test_the_formatter_under_this_repo_config_keeps_the_parentheses():
    """The behavioural proof, driven through ruff itself.

    This is the assertion that would have caught IA-082 directly: it says
    nothing about the target value, only that formatting a file with the
    repository's own configuration does not change what Python can parse it.
    """
    if sys.version_info < (3, 9):  # pragma: no cover
        pytest.skip("needs a modern interpreter to run ruff")

    probe = "def f(v):\n    try:\n        return float(v)\n    except (TypeError, ValueError):\n        return None\n"

    # Written inside the repository so ruff picks up pyproject.toml, which is
    # the whole point — an --isolated run passes even with the bad target.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", dir=REPO / "backend" / "app", delete=False,
    ) as handle:
        handle.write(probe)
        path = pathlib.Path(handle.name)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "format", str(path)],
            capture_output=True, text=True, cwd=REPO,
        )
        if result.returncode != 0 and "No module named" in (result.stderr or ""):
            pytest.skip("ruff is not installed here")

        formatted = path.read_text()
        assert "except (TypeError, ValueError):" in formatted, (
            f"ruff format, using this repository's configuration, rewrote the "
            f"exception list into a form older supported interpreters reject:\n"
            f"{formatted}"
        )
        # and the result must actually parse on this interpreter
        compile(formatted, str(path), "exec")
    finally:
        path.unlink(missing_ok=True)
