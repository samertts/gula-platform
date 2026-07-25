# Repository Security Configuration

**Version:** 1.0  
**Applies to:** github.com/samertts/gula-platform

## Security Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Pre-commit | detect-secrets | Block secrets before commit |
| Pre-commit | Gitleaks | Deep secret pattern matching |
| Pre-commit | pre-commit-hooks | Generic file hygiene |
| CI/CD | Secret Scanning Workflow | Scan every PR |
| CI/CD | Gitleaks CI | Full history scan on push |
| CI/CD | Dependency Review | Block vulnerable deps |
| CI/CD | CodeQL | Code quality & security |
| GitHub | Secret Scanning | Automatic push protection |
| GitHub | Push Protection | Block secrets on push |
| GitHub | Dependabot | Automated dependency updates |

## Git Configuration

### .gitignore

Covers: `.env`, `*.env.local`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.jks`,
`secrets/`, `credentials/`, `venv/`, `node_modules/`

### .gitattributes

- Auto-detects text vs binary files
- Sets LF line endings for shell scripts
- Marks `.env` as `linguist-generated=true`

### Pre-commit Hooks

Run `pre-commit run --all-files` to scan the entire repository.

## GitHub Protection Rules

### Branch Protection (main)

- Require pull request reviews
- Require status checks (all CI gates)
- Require up-to-date branches
- Include administrators
- Require signed commits
- Require linear history

### Push Protection

GitHub Push Protection is enabled for:
- API keys (AWS, Azure, GCP, OpenAI, etc.)
- Database connection strings
- Private keys
- Authentication tokens
- High-entropy strings

## Monitoring

- Secret scanning alerts go to repository security tab
- Dependabot alerts go to repository security tab
- CodeQL alerts go to repository security tab
- All alerts notify security team via GitHub notifications

## Incident Response

If a secret is detected:

1. **BLOCK** the commit/push (pre-commit or push protection)
2. **ALERT** the committer and security team
3. **ROTATE** the exposed credential immediately
4. **REMEDIATE** using git-filter-repo if already in history
5. **DOCUMENT** in docs/security/SECRET_ROTATION_PLAN.md

## Compliance

- OWASP ASVS V2: Authentication Verification Requirements
- OWASP ASVS V3: Session Management Verification Requirements
- OWASP ASVS V8: Data Protection Verification Requirements
- NIST SP 800-53: Access Control
- ISO 27001: A.9 Access Control

## Verification Checklist

- [ ] `git log --all --diff-filter=A --name-only | grep -iE '\.env$'` returns empty
- [ ] No `*.pem`, `*.key` files tracked in git
- [ ] `.secrets.baseline` exists and is current
- [ ] Pre-commit hooks installed and passing
- [ ] GitHub Secret Scanning enabled
- [ ] Dependabot configured
- [ ] CodeQL configured
- [ ] Branch protection rules active
