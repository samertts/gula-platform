"""SBOM Generator — SPDX 2.3 JSON

Scans backend/requirements.txt, services/*/pyproject.toml (or requirements.txt),
and all package.json files to produce a consolidated SPDX 2.3 JSON SBOM.

Usage:
    python scripts/generate_sbom.py [--output docs/sbom/latest.sbom.json]

Returns exit code 0 on success, 1 on failure.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "sbom" / "latest.sbom.json"
SPDX_VERSION = "SPDX-2.3"
SPDX_DATA_LICENSE = "CC0-1.0"
DOCUMENT_NAMESPACE_BASE = "https://gula-platform/sbom"


def _parse_requirements_line(line: str) -> dict[str, str | None] | None:
    """Parse a single line from a pip requirements.txt file.

    Handles:
      - package>=1.0.0
      - package==1.0.0
      - package~=1.0.0
      - package!=1.0.0
      - package<=1.0.0
      - package<1.0.0
      - package>1.0.0
      - package  (no version pin — uses latest)
      - package>=1.0.0,<2.0.0
      - package[extra]>=1.0.0
      - Comments (#) and blank lines are ignored
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    extras_match = re.match(r"^([a-zA-Z0-9_.-]+)", line)
    if not extras_match:
        return None

    pkg_name = extras_match.group(1)
    ver_match = re.search(r"([><=!]+)\s*([a-zA-Z0-9.*_-]+)", line)
    version: str | None = ver_match.group(2) if ver_match else None
    if version and version.endswith(".*"):
        version = version[:-2]
    return {"name": pkg_name, "version": version}


def _parse_pyproject_deps(pyproject_path: Path) -> list[dict[str, str | None]]:
    """Parse dependencies from a pyproject.toml [project] dependencies field."""
    deps: list[dict[str, str | None]] = []
    try:
        text = pyproject_path.read_text(encoding="utf-8")
    except Exception:
        return deps

    in_deps = False
    bracket_depth = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("dependencies = ["):
            in_deps = True
            bracket_depth += stripped.count("[")
            stripped = stripped[stripped.index("[") + 1 :]
            if bracket_depth == 0:
                in_deps = False
            continue
        if in_deps:
            bracket_depth += stripped.count("[") - stripped.count("]")
            if bracket_depth <= 0:
                in_deps = False
                if stripped.rstrip().endswith("]"):
                    stripped = stripped.rstrip()[:-1].strip()
                else:
                    continue
            cleaned = stripped.strip().rstrip(",").strip("\"'")
            if cleaned:
                parsed = _parse_requirements_line(cleaned)
                if parsed:
                    deps.append(parsed)
    return deps


def _get_package_license_via_pip(pkg_name: str) -> str | None:
    """Attempt to fetch a package's license by querying pip show."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.lower().startswith("license:"):
                    lic = line.split(":", 1)[1].strip()
                    return lic if lic and lic != "UNKNOWN" else None
    except Exception:
        pass
    return None


def _get_npm_license_via_cli(pkg_name: str, version: str | None) -> str | None:
    """Try to determine an npm package's license by heuristic matching."""
    known_licenses: dict[str, str] = {
        "express": "MIT",
        "react": "MIT",
        "react-dom": "MIT",
        "tailwindcss": "MIT",
        "zod": "MIT",
        "typescript": "Apache-2.0",
        "uuid": "MIT",
        "axios": "MIT",
        "cors": "MIT",
        "helmet": "MIT",
        "compression": "MIT",
        "jsonwebtoken": "MIT",
        "dotenv": "BSD-2-Clause",
        "redis": "MIT",
        "mysql2": "MIT",
        "@trpc/server": "MIT",
        "@trpc/client": "MIT",
        "@trpc/react-query": "MIT",
        "@tanstack/react-query": "MIT",
        "@tanstack/react-query-devtools": "MIT",
        "bcryptjs": "MIT",
        "superjson": "MIT",
    }
    return known_licenses.get(pkg_name)


def scan_requirements_txt(path: Path) -> list[dict[str, Any]]:
    """Scan a requirements.txt file for dependencies."""
    packages: list[dict[str, Any]] = []
    if not path.exists():
        return packages
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_requirements_line(line)
        if parsed and parsed["name"]:
            packages.append({
                "name": parsed["name"],
                "version": parsed["version"],
                "supplier": "PyPI",
                "license": _get_package_license_via_pip(parsed["name"]),
                "relationship": "DEPENDS_ON",
            })
    return packages


def scan_pyproject(path: Path) -> list[dict[str, Any]]:
    """Scan a pyproject.toml for project dependencies."""
    packages: list[dict[str, Any]] = []
    if not path.exists():
        return packages
    deps = _parse_pyproject_deps(path)
    for dep in deps:
        if dep["name"]:
            packages.append({
                "name": dep["name"],
                "version": dep["version"],
                "supplier": "PyPI",
                "license": _get_package_license_via_pip(dep["name"]),
                "relationship": "DEPENDS_ON",
            })
    return packages


def scan_service_dependencies() -> list[dict[str, Any]]:
    """Scan services/ subdirectories for pyproject.toml or requirements.txt."""
    packages: list[dict[str, Any]] = []
    services_dir = REPO_ROOT / "services"
    if not services_dir.is_dir():
        return packages
    for entry in sorted(services_dir.iterdir()):
        if not entry.is_dir():
            continue
        pyproject = entry / "pyproject.toml"
        requirements = entry / "requirements.txt"
        if pyproject.exists():
            packages.extend(scan_pyproject(pyproject))
        if requirements.exists():
            packages.extend(scan_requirements_txt(requirements))
    return packages


def scan_package_json(path: Path) -> list[dict[str, Any]]:
    """Scan a package.json for JavaScript dependencies."""
    packages: list[dict[str, Any]] = []
    if not path.exists():
        return packages
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return packages

    all_deps: dict[str, str] = {}
    all_deps.update(data.get("dependencies", {}))
    all_deps.update(data.get("devDependencies", {}))

    for name, version_spec in all_deps.items():
        version = version_spec.lstrip("^~>=<!")
        packages.append({
            "name": name,
            "version": version if version != version_spec else version_spec,
            "supplier": "npm",
            "license": _get_npm_license_via_cli(name, version),
            "relationship": "DEV_DEPENDENCY_OF" if name in data.get("devDependencies", {}) else "DEPENDS_ON",
        })
    return packages


def scan_all_package_json() -> list[dict[str, Any]]:
    """Scan all package.json files under the repo root."""
    packages: list[dict[str, Any]] = []
    for path in REPO_ROOT.rglob("package.json"):
        if "node_modules" in str(path):
            continue
        packages.extend(scan_package_json(path))
    return packages


def build_spdx_document(packages: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an SPDX 2.3 JSON document from the package list."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc_namespace = f"{DOCUMENT_NAMESPACE_BASE}/{now}"

    unique_packages: dict[str, dict[str, Any]] = {}
    for pkg in packages:
        key = f"{pkg['name']}@{pkg['version'] or 'latest'}"
        if key not in unique_packages:
            unique_packages[key] = pkg
        else:
            existing = unique_packages[key]
            if pkg.get("license") and not existing.get("license"):
                existing["license"] = pkg["license"]

    spdx_packages: list[dict[str, Any]] = []
    spdx_relationships: list[dict[str, Any]] = []
    for idx, (key, pkg) in enumerate(unique_packages.items()):
        spdx_id = f"SPDXRef-Package-{idx}"
        pkg_name = pkg["name"]
        pkg_version = pkg.get("version") or "0.0.0"
        pkg_license = pkg.get("license") or "NOASSERTION"
        pkg_supplier = pkg.get("supplier", "NOASSERTION")

        if pkg_supplier == "PyPI":
            download_location = f"https://pypi.org/project/{pkg_name}/{pkg_version}/"
        elif pkg_supplier == "npm":
            download_location = f"https://www.npmjs.com/package/{pkg_name}/v/{pkg_version}"
        else:
            download_location = "NOASSERTION"

        spdx_packages.append({
            "SPDXID": spdx_id,
            "name": pkg_name,
            "versionInfo": pkg_version,
            "supplier": f"Organization: {pkg_supplier}" if pkg_supplier not in ("NOASSERTION",) else "NOASSERTION",
            "downloadLocation": download_location,
            "filesAnalyzed": False,
            "licenseConcluded": pkg_license if pkg_license != "NOASSERTION" else "NOASSERTION",
            "licenseDeclared": pkg_license if pkg_license != "NOASSERTION" else "NOASSERTION",
            "copyrightText": "NOASSERTION",
        })

        spdx_relationships.append({
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relatedSpdxElement": spdx_id,
            "relationshipType": pkg.get("relationship", "DEPENDS_ON"),
        })

    doc = {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": SPDX_DATA_LICENSE,
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "GULA Platform SBOM",
        "documentNamespace": doc_namespace,
        "creationInfo": {
            "created": now,
            "creators": [
                "Tool: gula-sbom-generator",
                f"Organization: GULA Platform ({DOCUMENT_NAMESPACE_BASE})",
            ],
        },
        "packages": spdx_packages,
        "relationships": spdx_relationships,
    }
    return doc


def main() -> int:
    output_path = DEFAULT_OUTPUT
    if len(sys.argv) > 1:
        flag = sys.argv[1]
        if flag.startswith("--output="):
            output_path = REPO_ROOT / flag.split("=", 1)[1]
        elif flag == "--output" and len(sys.argv) > 2:
            output_path = REPO_ROOT / sys.argv[2]
        elif flag in ("-h", "--help"):
            print("Usage: python scripts/generate_sbom.py [--output <path>]")
            return 0

    all_packages: list[dict[str, Any]] = []

    # Backend Python deps
    all_packages.extend(scan_requirements_txt(REPO_ROOT / "backend" / "requirements.txt"))

    # Service Python deps
    all_packages.extend(scan_service_dependencies())

    # JavaScript deps from all package.json files
    all_packages.extend(scan_all_package_json())

    doc = build_spdx_document(all_packages)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    pkg_count = len(doc["packages"])
    print(f"SBOM written to {output_path}")
    print(f"  Packages: {pkg_count}")
    print(f"  Relationships: {len(doc['relationships'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
