#!/usr/bin/env python3
# ruff: noqa: T201
"""Fail closed when the CI SBOM artifact is missing or structurally invalid."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_sbom_artifact.py <cyclonedx-json-path>", file=sys.stderr)
        return 2

    artifact_path = Path(argv[1])
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"SBOM_INVALID: cannot read CycloneDX JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict):
        print("SBOM_INVALID: root must be a JSON object", file=sys.stderr)
        return 1
    if payload.get("bomFormat") != "CycloneDX":
        print("SBOM_INVALID: bomFormat must be CycloneDX", file=sys.stderr)
        return 1
    if not isinstance(payload.get("specVersion"), str) or not payload["specVersion"]:
        print("SBOM_INVALID: specVersion is required", file=sys.stderr)
        return 1

    components = payload.get("components")
    if not isinstance(components, list) or not components:
        print("SBOM_INVALID: components must be a non-empty list", file=sys.stderr)
        return 1
    if any(not isinstance(component, dict) or not component.get("name") for component in components):
        print("SBOM_INVALID: each component must be an object with a name", file=sys.stderr)
        return 1

    print(
        "SBOM_OK: "
        f"CycloneDX {payload['specVersion']} with {len(components)} components"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
