# CI/CD Security Report

## GitHub Actions Workflows

| Workflow | Purpose | Security Checks |
|----------|---------|----------------|
| ci.yml | Build & test | None (no SAST/DAST) |
| deploy.yml | Production deployment | None |
| canary-deploy.yml | Canary deployment | None |
| blue-green-deploy.yml | Blue-green deployment | None |
| rollback.yml | Rollback | None |
| auto-rollback.yml | Auto-rollback | None |
| codeql-analysis.yml | CodeQL scanning | ✅ Present |
| dependency-review.yml | Dependency review | ✅ Present |
| quality-gate.yml | Quality gate | ✅ Present |
| formatting.yml | Code formatting | ✅ Present |
| scorecard.yml | OpenSSF Scorecard | ✅ Present |
| constitution-compliance.yml | Constitution compliance | ✅ Present |
| release.yml | Release | None |
| frontend-e2e.yml | E2E tests | None |

## Security Gaps in CI/CD

### CI-01: No SAST Scanning in CI
**Severity:** High
**Description:** Bandit, Semgrep, or similar SAST tools not integrated into CI pipeline
**Recommendation:** Add Bandit for Python, Semgrep for multi-language scanning

### CI-02: No Container Image Scanning
**Severity:** Critical
**Description:** Trivy or Grype not run on built images before push
**Recommendation:** Add `trivy image` scan step after Docker build

### CI-03: No Image Signing
**Severity:** Critical
**Description:** Images pushed without cosign signing
**Recommendation:** Add `cosign sign` step after build

### CI-04: No SBOM Generation
**Severity:** High
**Description:** No Syft SBOM generated in CI/CD
**Recommendation:** Add `syft` SBOM generation step

### CI-05: No IaC Scanning
**Severity:** High
**Description:** Checkov not run in CI/CD
**Recommendation:** Add Checkov scan for Terraform/K8s

### CI-06: No Secret Scanning in CI
**Severity:** High
**Description:** Gitleaks not run in CI/CD
**Recommendation:** Add `gitleaks detect` step

### CI-07: No DAST Scanning
**Severity:** Medium
**Description:** No DAST in CI/CD
**Recommendation:** Add ZAP or similar DAST tool

### CI-08: Weak Pipeline Permissions
**Severity:** High
**Description:** Workflows may have excessive permissions
**Recommendation:** Apply principle of least privilege to GITHUB_TOKEN

## Recommendations

Add the following to `.github/workflows/ci.yml`:

```yaml
- name: Run SAST (Bandit)
  run: bandit -r backend/app -f json

- name: Run IaC Scan (Checkov)
  run: checkov -d terraform -d k8s

- name: Scan for Secrets
  run: gitleaks detect --no-git -v

- name: Scan Docker Image
  run: trivy image --severity CRITICAL,HIGH ${{ env.IMAGE_NAME }}

- name: Generate SBOM
  run: syft ${{ env.IMAGE_NAME }} -o spdx-json > sbom.json

- name: Sign Image
  run: cosign sign --key ${{ secrets.COSIGN_KEY }} ${{ env.IMAGE_NAME }}
```
