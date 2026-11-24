"""Static guards for the WS-E client integration package.

These guards assert that the new package stays a declaration/validation layer:
no client code, no activation surface, no persistence, no skipped tests.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest
from app.health_core.client_integration import manifest_for
from app.health_core.client_integration.platforms import Platform
from app.health_core.client_integration.validators import (
    REPO_ROOT,
    validate_manifest,
)
from app.health_core.common import HealthCoreError

PACKAGE_DIR = REPO_ROOT / "backend/app/health_core/client_integration"
TEST_FILES = (
    REPO_ROOT / "backend/tests/health_core/test_client_integration_manifests.py",
    REPO_ROOT / "backend/tests/health_core/test_client_integration_guards.py",
)

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "abc",
    "collections",
    "dataclasses",
    "enum",
    "pathlib",
    "types",
    "app",
}

FORBIDDEN_TOKENS = (
    "APIRouter",
    "include_router",
    "FastAPI(",
    "@router.",
    "sqlalchemy",
    "alembic",
    "redis",
    "kafka",
    "httpx",
    "requests.",
    "socket",
    "subprocess",
    "os.system",
    "write_text",
    "unlink(",
    "rmtree",
)


def _package_sources() -> tuple[tuple[Path, str], ...]:
    return tuple(
        (path, path.read_text(encoding="utf-8"))
        for path in sorted(PACKAGE_DIR.glob("*.py"))
    )


def test_package_contains_only_the_declared_modules() -> None:
    assert {path.name for path in PACKAGE_DIR.glob("*.py")} == {
        "__init__.py",
        "manifests.py",
        "observations.py",
        "platforms.py",
        "report.py",
        "validators.py",
    }
    assert not any(PACKAGE_DIR.rglob("*migration*"))


def test_new_package_imports_only_stdlib_and_health_core() -> None:
    for path, source in _package_sources():
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = {node.module.split(".")[0]}
            else:
                continue
            assert roots <= ALLOWED_IMPORT_ROOTS, (path.name, roots)


def test_new_package_has_no_route_persistence_or_network_surface() -> None:
    for path, source in _package_sources():
        lowered = source.lower()
        for token in FORBIDDEN_TOKENS:
            assert token.lower() not in lowered, (path.name, token)
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "exec", "eval", "compile"}

    app_dir = REPO_ROOT / "backend/app"
    for activation_file in (app_dir / "factory.py", app_dir / "main.py"):
        if activation_file.exists():
            assert "client_integration" not in activation_file.read_text(encoding="utf-8")


def test_new_test_files_have_no_skips_and_real_assertions() -> None:
    for path in TEST_FILES:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            assert not (
                isinstance(node, ast.Attribute)
                and node.attr in {"skip", "skipif", "xfail"}
                and isinstance(node.value, ast.Attribute)
                and node.value.attr == "mark"
            ), (path.name, node.attr)
        test_functions = [
            node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name.startswith("test_")
        ]
        assert test_functions, path
        for function in test_functions:
            body = ast.dump(ast.Module(body=function.body, type_ignores=[]))
            assert "Assert" in body or "pytest.raises" in source, function.name


def test_validation_errors_are_structured_not_silent() -> None:
    bad = replace(manifest_for(Platform.EXPO), adapter_bound=True)
    validation = validate_manifest(bad, repo_root=REPO_ROOT)
    assert not validation.is_valid
    with pytest.raises(HealthCoreError) as exc_info:
        validation.raise_if_invalid()
    payload = exc_info.value.to_dict()
    assert payload["code"] == "HEALTH_CORE_ERROR"
    assert payload["details"]["platform"] == Platform.EXPO.value
    assert "UNVERIFIED_ADAPTER_CLAIM" in payload["details"]["errors"]
