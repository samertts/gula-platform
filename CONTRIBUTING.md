# Contributing to GULA Platform

Thank you for your interest in contributing! We welcome contributions from
everyone. Please take a moment to review this guide.

## Quick Start

```bash
git clone https://github.com/samertts/gula-platform
cd gula-platform
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env  # edit as needed
make up
```

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker and Docker Compose
- PostgreSQL 16 (if running outside Docker)
- Redis 7 (if running outside Docker)

### Local Development

```bash
# Install pre-commit hooks
pip install pre-commit && pre-commit install

# Run the full stack
make up

# Run tests
cd backend && python -m pytest tests/ -v

# Run linting
ruff check backend/app/

# Run type checking
mypy backend/app/
```

## Development Workflow

1. **Fork and clone** the repository
2. **Create a feature branch**: `git checkout -b feat/your-feature-name`
3. **Make your changes**
4. **Run tests**: `cd backend && python -m pytest tests/ -v`
5. **Lint**: `ruff check backend/app/`
6. **Type check**: `mypy backend/app/`
7. **Verify syntax**: `python -m py_compile backend/app/main.py`
8. **Commit** using conventional commits (see below)
9. **Push** and create a pull request

## Branch Strategy

| Branch Pattern | Purpose |
|----------------|---------|
| `main` | Production-ready code |
| `release/*` | Release branches |
| `feat/*` | New features |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation changes |
| `chore/*` | Maintenance tasks |
| `security/*` | Security fixes |

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `style` — Code style (formatting, etc.)
- `refactor` — Code restructuring
- `perf` — Performance improvement
- `test` — Adding or updating tests
- `chore` — Maintenance tasks
- `ci` — CI/CD changes
- `security` — Security fixes
- `revert` — Reverting changes

### Examples

```
feat(auth): add OAuth2 social login support
fix(api): correct pagination offset calculation
docs(readme): update deployment instructions
security(auth): patch JWT token validation
```

## Pull Request Process

1. Ensure all tests pass (`make test` or `cd backend && python -m pytest tests/ -v`)
2. Ensure linting passes (`ruff check backend/app/`)
3. Ensure type checking passes (`mypy backend/app/`)
4. Update documentation if your changes affect user-facing features
5. Fill out the [pull request template](.github/PULL_REQUEST_TEMPLATE.md)
6. Request review from a maintainer
7. Address review feedback
8. Once approved, a maintainer will merge your PR

### PR Checklist

- [ ] Code follows project coding standards
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] All CI checks pass
- [ ] Conventional commit message used

## Coding Standards

### Python

- Python 3.12+ with `from __future__ import annotations`
- FastAPI async patterns
- SQLAlchemy 2.0 async style (`select()`, not `session.query()`)
- All mutations write to AuditLog
- All patient data queries filter by `lab_id`
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints everywhere
- Use `ruff` for linting and formatting

### TypeScript / React

- Use TypeScript in strict mode
- Follow the existing component patterns
- Use React hooks for state management
- Use Tailwind CSS for styling

### Frontend Development Setup

```bash
# Navigate to the frontend directory
cd frontend-v3

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Type check
npx tsc --noEmit

# Lint
npm run lint
```

### Environment Variables

Key environment variables are documented in `.env.example`. For local development:

```bash
# Required for backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gula
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<generate-a-random-secret>
ENCRYPTION_KEY=<generate-a-fernet-key>
NID_HMAC_KEY=<generate-a-random-hmac-key>

# Required for frontend
VITE_API_URL=http://localhost:8080
```

Generate keys using `make secrets-gen`.

### Code Review Guidelines

When reviewing pull requests:

1. **Functionality**: Does the code do what it claims?
2. **Correctness**: Are there edge cases or logic errors?
3. **Security**: Does the change introduce vulnerabilities?
4. **Performance**: Are there obvious performance issues?
5. **Test coverage**: Are there tests for the new code?
6. **Documentation**: Are changes documented?
7. **Constitution compliance**: Does the change follow Platform Constitution rules?

Reviewers should be constructive and specific in their feedback.

## Testing Requirements

- All new features must include tests
- Bug fixes must include a test that reproduces the bug
- Tests should use in-memory repositories where possible
- CI must pass before merging

### Test Categories

```bash
# Unit tests (no DB, no network)
pytest tests/ -m unit

# Integration tests (require DB)
pytest tests/ -m integration

# All tests
cd backend && python -m pytest tests/ -v
```

## Documentation Expectations

- All new features must include documentation
- Update relevant README sections
- Add or update ADRs for architectural decisions
- Document API changes in the appropriate locations

### Documentation Files

- `README.md` — Project overview and quick start
- `ARCHITECTURE.md` — System architecture
- `CLAUDE.md` — Full developer guide
- `docs/` — ADRs, specifications, and reference

## Platform Constitution Compliance

Every contribution MUST comply with PROGRAM-CONSTITUTION-001:

- **Free First** — Always search for free solution before paid
- **Open Source First** — Prefer open source over proprietary
- **Self-Hosted First** — Self-hosted before hosted SaaS
- **No Vendor Lock-In** — Every dependency MUST have an abstraction layer
- **Reuse Before Build** — Never duplicate existing functionality
- **Zero Paid Dependency** — Paid dependencies require documented exception

Full policy: `docs/constitution/COST_GOVERNANCE.md`

## Quality Gates (pre-commit)

Every commit must pass:
- **pytest** — all tests green
- **ruff** — no errors (style warnings OK)
- **mypy** — no type errors
- **bandit** — no security issues
- **constitution** — `make constitution-check` verifies compliance

## Getting Help

- Check [SUPPORT.md](SUPPORT.md) for support resources
- Open a [GitHub Discussion](https://github.com/samertts/gula-platform/discussions)
- Join the community conversations

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Architecture

See `ARCHITECTURE.md` for the monolith-first deployment model.
See `CLAUDE.md` for the comprehensive developer guide.
