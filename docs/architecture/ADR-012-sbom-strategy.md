# ADR-012: SBOM Strategy

**Status:** Accepted
**Date:** 2026-07-18
**Constitutional Basis:** ENGINEERING_CONSTITUTION.md §9.7, PLATFORM-CONSTITUTION.md §4

## Context

The Engineering Constitution §9.7 (Supply Chain Security) requires an SBOM (Software Bill of Materials) for every build, with dependencies pinned and hash-verified. The GULA platform has multiple dependency sources: Python (requirements.txt, pyproject.toml), JavaScript (package.json), and service-level dependencies. A consistent, automated approach is needed to generate and maintain SBOMs across all components.

## Decision

Adopt a **script-based SBOM generation** approach using SPDX 2.3 JSON format:

1. **Generation:** `scripts/generate_sbom.py` scans all dependency files and produces `docs/sbom/latest.sbom.json`
2. **Format:** SPDX 2.3 JSON — the most widely adopted open standard
3. **Frequency:** Generated on every CI build and on-demand via `make sbom`
4. **Storage:** Committed to the repository at `docs/sbom/latest.sbom.json` for traceability
5. **Scope:** Python deps (backend + services), JavaScript deps (all package.json files), system packages (when running in Docker)

### SBOM Contents

- Package name, version, supplier (if detectable)
- License information (from package metadata, NOT detected via scanning)
- Dependency relationships (direct vs. transitive)
- Package download location (PyPI, npm)
- Document namespace (unique per build)

## Rationale

- **Automation:** Script-based approach integrates into existing CI without external tool dependencies
- **Standard compliance:** SPDX is the ISO-recognized SBOM standard (ISO/IEC 5962:2021)
- **Traceability:** Committed SBOMs provide a historical record of dependency changes
- **Cost:** No external service dependency (e.g., Dependency-Track, Snyk) required for SBOM generation
- **Flexibility:** Script can be extended to include container image layers and system packages

## Consequences

- `scripts/generate_sbom.py` is the single source of truth for SBOM generation
- SBOM is committed to the repo and updated on every significant dependency change
- CI pipeline will include SBOM generation as a step
- License compliance scanning (e.g., for GPL/AGPL detection) uses the SBOM as input
- Future enhancement: SBOM signing with GPG and automated vulnerability correlation

## Compliance

- SBOM is generated and validated on every CI build
- `docs/sbom/latest.sbom.json` exists and is valid SPDX 2.3 JSON
- SBOM covers all production dependencies
- SBOM is reviewed when dependencies change significantly
