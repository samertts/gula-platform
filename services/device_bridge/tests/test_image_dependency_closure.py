"""Every package the code imports must be one the image installs.

IA-051 (P2) — DISCOVERED, REPRODUCED, FIXED, VERIFIED. Closes the half of
IA-044 that was recorded as UNVERIFIED because no Docker daemon was available.

IA-044 fixed a `ModuleNotFoundError: No module named 'backend'` that only the
image hit: the Dockerfile copies `app/` and nothing else, while every local test
run has the repository root on PYTHONPATH. That same blind spot had a second
occupant. `app/connectors/base.py` opens a serial analyzer with

    from serial import Serial  # pyserial runtime dependency

a function-local import, so a missing pyserial broke the *first serial
connection* rather than startup — and the package was declared nowhere: not in
pyproject, not in the Dockerfile's pip install. Reading a physical serial
analyzer is half this service's purpose.

REPRODUCED, in a venv holding exactly the Dockerfile's declared package set:

    6/6 pyserial, which app/connectors/base.py needs to open a serial analyzer
        pyserial MISSING - a serial analyzer cannot be opened in this image.

FIXED: pyserial is declared in both pyproject.toml and the Dockerfile's pip
install, and the same probe now reports `pyserial present`.

VERIFIED without a daemon by `scripts/verify_image_equivalent.sh`, which mirrors
the image's two constraints — only `app/` importable, only the Dockerfile's
packages installed — and then runs the Dockerfile's CMD, the compose
healthcheck verbatim, a real ASTM ingest, an unauthenticated read, and the
pyserial check. It reads the package list *out of the Dockerfile* rather than
carrying a copy, because a copy drifts and then the script proves something
about the copy.

This test is the fast static half: it compares the third-party imports under
`app/` against the Dockerfile's declared set on every run, so a new undeclared
dependency fails in milliseconds instead of waiting for someone to run the
script or deploy the image.
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from _dockerfile_packages import packages as dockerfile_packages

_SERVICE = pathlib.Path(__file__).resolve().parents[1]
_APP = _SERVICE / "app"
_DOCKERFILE = _SERVICE / "Dockerfile"

# Import name -> distribution name, for the cases where they differ. Kept
# explicit: guessing this mapping is how a dependency check quietly stops
# checking.
_IMPORT_TO_DISTRIBUTION = {
    "serial": "pyserial",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "jose": "python-jose",
    "jwt": "pyjwt",
}


def _third_party_imports() -> dict[str, set[str]]:
    """Top-level third-party module names imported under app/, with their files."""
    stdlib = set(sys.stdlib_module_names)
    found: dict[str, set[str]] = {}
    for path in _APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text())
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
        for name in names - stdlib - {"app"}:
            found.setdefault(name, set()).add(path.relative_to(_SERVICE).as_posix())
    return found


def _declared_distributions() -> set[str]:
    """Distribution names the Dockerfile's pip install declares, normalised."""
    requirements = dockerfile_packages(_DOCKERFILE.read_text())
    names = set()
    for requirement in requirements:
        name = requirement.split(">=")[0].split("==")[0].split("[")[0].strip()
        names.add(name.lower().replace("_", "-"))
    return names


def test_every_imported_package_is_declared_by_the_dockerfile():
    """The check that would have caught pyserial on the day it was first
    imported, instead of on the day someone connected a serial analyzer."""
    declared = _declared_distributions()
    missing = {}
    for module, files in sorted(_third_party_imports().items()):
        distribution = _IMPORT_TO_DISTRIBUTION.get(module, module).lower().replace("_", "-")
        if distribution not in declared:
            missing[module] = (distribution, sorted(files))

    assert missing == {}, (
        "app/ imports packages the image does not install: "
        + "; ".join(
            f"{module} (pip name {dist}) from {files}" for module, (dist, files) in missing.items()
        )
        + f". Declared: {sorted(declared)}"
    )


def test_pyserial_is_declared_in_both_places():
    """pyproject declares what the service needs; the Dockerfile's explicit pip
    list is what the image actually installs, and it does not read pyproject.
    Both have to say it, which is why IA-044 left this half open."""
    assert "pyserial" in (_SERVICE / "pyproject.toml").read_text()
    assert "pyserial" in _DOCKERFILE.read_text()
    assert "pyserial" in _declared_distributions()


def test_the_serial_import_is_still_function_local():
    """Why the gap was invisible: a module-level import would have broken
    startup and been caught immediately. If this ever becomes module-level the
    failure mode changes, and this finding needs re-reading."""
    source = (_APP / "connectors" / "base.py").read_text()
    tree = ast.parse(source)
    module_level = {
        alias.name.split(".")[0]
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "serial" not in module_level
    assert "from serial import Serial" in source


def test_the_package_reader_reads_the_dockerfile_and_not_a_copy():
    """The script's proof is only about the image if the list comes out of the
    Dockerfile. A transcribed list drifts."""
    requirements = dockerfile_packages(_DOCKERFILE.read_text())
    assert len(requirements) >= 5
    assert any(r.startswith("fastapi") for r in requirements)
    assert any(r.startswith("pyserial") for r in requirements)

    with pytest.raises(SystemExit):
        dockerfile_packages("FROM python:3.14-slim\nWORKDIR /app\n")


def test_the_image_equivalent_script_is_present_and_executable():
    """It is the only runtime proof available without a Docker daemon, so it
    must not quietly disappear."""
    script = _SERVICE / "scripts" / "verify_image_equivalent.sh"
    assert script.is_file()
    assert script.stat().st_mode & 0o111, "the script is not executable"
    text = script.read_text()
    # The steps this finding and IA-044/IA-050 rest on.
    assert "import app.main" in text
    assert "uvicorn app.main:app" in text
    assert "urllib.request.urlopen" in text, "the compose healthcheck step is gone"
    assert "device_abnormal_flags" in text, "the IA-050 assertion is gone"
    assert "401" in text, "the unauthenticated-read step is gone"
    assert "import serial" in text, "the pyserial step is gone"
    # NP-57 caught this missing: the reader's own test exercised the function,
    # not the script's use of it, so replacing the script's call with a
    # hardcoded list left every test green while the proof became a proof about
    # the hardcoded list.
    assert "scripts/_dockerfile_packages.py" in text, (
        "the script no longer derives its package set from the Dockerfile, so "
        "what it installs can drift from what the image installs"
    )
    assert '"fastapi>=0.115.0"' not in text, (
        "the script carries a transcribed package list again"
    )
