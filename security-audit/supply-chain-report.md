# Supply Chain Security Report

## Dependency Sources

| Source | Type | Count |
|--------|------|-------|
| PyPI (Python) | Direct | 20+ packages |
| npm (Node.js) | Direct | 30+ packages |
| Docker Hub | Container images | Multiple base images |
| GitHub Container Registry | Internal images | Backend images |
| Cloudflare R2 | Object storage | Reports storage |
| Supabase | Database (optional) | Analytics |
| Google Gemini | AI API | Clinical AI |
| Firebase (frontend-v2) | Various | Mobile push, auth |

## Supply Chain Risks

### SCM-01: No Dependency Pinning Verification
**Severity:** High
**Description:** Python requirements use `>=` version ranges, not pinned exact versions
**Impact:** Different builds may resolve different dependency versions
**Affected:** All `requirements.txt` files
**Remediation:** Pin exact versions in lock files, verify with `pip-audit`

### SCM-02: No Software Bill of Materials (SBOM)
**Severity:** High
**Description:** No SBOM generated in CI/CD pipeline
**Impact:** Cannot quickly identify affected components during vulnerability disclosure
**Remediation:** Generate SBOM with Syft in CI/CD, publish to dependency track

### SCM-03: Frontend-v2 Firebase Configuration Exposed
**Severity:** High
**Description:** `firebase-applet-config.json` and `firebase-blueprint.json` in repository
**Impact:** Firebase project configuration exposed, enabling targeted attacks
**Remediation:** Remove Firebase configs from repository; inject via environment

### SCM-04: Node Modules Included in Build Context
**Severity:** Medium
**Description:** `.dockerignore` may not exclude `node_modules` from build context
**Impact:** Increased build time, potential secret leakage
**Remediation:** Verify `.dockerignore` excludes `node_modules`

### SCM-05: No Registry Authentication for npm
**Severity:** Medium
**Description:** No `.npmrc` with registry authentication
**Impact:** Risk of dependency confusion attack
**Remediation:** Configure registry authentication in CI/CD

### SCM-06: Third-Party Docker Images Not Pinned by Digest
**Severity:** High
**Description:** Docker images referenced by tag (e.g., `postgres:17-alpine`) not by digest
**Impact:** Vulnerable to tag mutability attacks
**Remediation:** Pin images by digest: `postgres@sha256:abc123...`

## Supply Chain Recommendations

1. Generate SBOM in CI/CD pipeline using Syft
2. Pin all third-party Docker images by digest
3. Pin all Python dependencies to exact versions
4. Add Dependabot for automated dependency updates
5. Implement dependency license compliance checking
6. Add OSSF Scorecard checks
7. Add SLSA provenance attestation
8. Configure npm registry authentication
9. Remove unnecessary Firebase configuration files
10. Add dependency vulnerability monitoring (Dependency-Track)
11. Verify package signatures where available
12. Implement regular dependency audit process
