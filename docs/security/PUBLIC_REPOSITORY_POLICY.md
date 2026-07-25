# Public Repository Security Policy

**Version:** 1.0  
**Classification:** PUBLIC  
**Effective Date:** 2026-07-25

## Scope

This policy applies to all contributors to the GULA Platform repository,
which is PUBLIC. Every commit is immediately visible to the internet.

## Zero-Tolerance Policy

The following are STRICTLY PROHIBITED:

1. **Committing secrets** of any kind
2. **Committing .env files** or credential files
3. **Hardcoding** passwords, API keys, tokens, or private keys
4. **Logging secrets** or sensitive configuration values
5. **Including credentials** in URLs, connection strings, or comments
6. **Storing secrets** in docker-compose default values

Violations result in immediate secret rotation and potential access revocation.

## Mandatory Controls

### Pre-commit (Enforced Locally)

Every developer MUST install pre-commit hooks:

```bash
pip install pre-commit detect-secrets
pre-commit install
```

Hooks check for: secrets, private keys, large files, merge conflicts, syntax errors

### Git History Cleanliness

- Only the latest commit should exist for any given change
- Use `git rebase` to squash commits before pushing
- Never include generated files, credentials, or sensitive data in any commit

### Environment Variable Usage

ALL configuration values MUST come from environment variables:

```python
# CORRECT
DATABASE_URL = os.environ["DATABASE_URL"]

# WRONG
DATABASE_URL = "postgresql://user:password@localhost:5432/db"
```

### Configuration Templates

Template files (`.env.example`) MUST use placeholder values:

```
DATABASE_URL=postgresql://user:CHANGE_ME_PASSWORD@host:5432/db
```

## CI/CD Security Gates

Every PR MUST pass before merge:

1. **Secret Scanning** — detect-secrets + Gitleaks scan
2. **Dependency Review** — no critical vulnerabilities
3. **CodeQL** — no critical/high severity findings
4. **Unit Tests** — all passing
5. **Linting** — ruff, mypy, eslint passing
6. **Build** — clean build

## Incident Reporting

Report any suspected secret exposure immediately:

1. Rotate the compromised credential
2. Open a security issue (use security issue template)
3. Notify the security team

## Approved Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| detect-secrets | Secret detection | `.secrets.baseline` |
| Gitleaks | Git history scanning | `.github/workflows/secret-scanning.yml` |
| GitHub Secret Scanning | Push protection | Repository Settings → Security |
| Dependabot | Dependency scanning | `.github/dependabot.yml` |
| CodeQL | Code quality | `.github/workflows/codeql-analysis.yml` |

## Enforcement

This policy is enforced through:
1. Pre-commit hooks (local enforcement)
2. GitHub Actions (CI enforcement)
3. GitHub Secret Scanning (server-side enforcement)
4. Branch protection rules (merge enforcement)
5. Periodic audits (quarterly secret scans)

## Review

This policy is reviewed quarterly and updated as needed.

Last Review: 2026-07-25  
Next Review: 2026-10-25
