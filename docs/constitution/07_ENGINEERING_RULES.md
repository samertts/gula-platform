# GULA Engineering Rules

## Code Quality

1. **All Python code must pass `py_compile` and `pyflakes` (select E9, F821) before commit.** This is enforced by the syntax-gate CI job.

2. **No commented-out code.** Delete it. Version control exists for history.

3. **No print statements in production code.** Use the structured logger (`logger = logging.getLogger("gula.module")`) with appropriate levels.

4. **Docstrings are required for public APIs** (route handlers, exported service methods, public classes). Internal methods do not require docstrings unless the logic is non-obvious. Inline implementation comments are prohibited — code should be self-documenting through clear naming and structure.

5. **Type hints are required for all function signatures.** Use `from __future__ import annotations` for forward references.

6. **Max line length is 120 characters.** Strings exceeding this should use implicit concatenation or parentheses.

7. **Imports are organized:** standard library → third-party → first-party. Within each group, alphabetical order.

## Project Structure

8. **`backend/app/`** is the production monolith. All routes, models, and services live here.

9. **`services/`** contains independent deployable services. Each service has its own `app/`, requirements, and Dockerfile.

10. **`frontend-v2/`** is the React + Firebase frontend. Components follow feature-based organization under `src/`.

11. **`docs/`** contains all documentation. Architecture decisions, constitution, and reference materials go here.

12. **`scripts/`** contains operational and development scripts. Scripts must be idempotent and well-documented.

## Database

13. **All schema changes require a new Alembic migration.** Existing migrations are never modified.

14. **Migrations must be idempotent.** Use `_has_table()`, `_has_column()`, and `_index_exists()` guards.

15. **New columns must be nullable or have a `server_default`.** Non-nullable columns without defaults break existing rows.

16. **The base migration `20250322_0000_create_base_schema.py` is immutable.**

17. **Every model must have `created_at` and optionally `updated_at` timestamp columns.**

## Testing

18. **Every service method must have at least one unit test.** Business logic in services is the primary testing target.

19. **Route handlers are tested through integration tests** that verify HTTP status codes, response shapes, and error conditions.

20. **Tests must not depend on external services** unless explicitly labeled as integration tests.

21. **Test data is created through factories or fixtures, never through production data.**

22. **`python -m py_compile app/main.py` must pass before any commit.** This is the minimum syntax gate.

## Git Conventions

23. **Commit messages follow conventional commits format:** `type(scope): description`. Types: feat, fix, refactor, test, docs, chore, ci, security.

24. **No commits to `main` except through PR.** Feature branches must be reviewed.

25. **No force pushes to shared branches.**

26. **Secrets are never committed.** Use `.env.example` for templates, `.env` for actual values (gitignored).

## Error Handling

27. **Domain errors use `DomainError` subclasses** with appropriate HTTP status codes and Arabic/English messages.

28. **Business logic errors are caught and translated to API errors at the route layer.** Raw exceptions never propagate to the client in production.

29. **Retryable errors (network, database transient, rate limits) are retried with exponential backoff.**

## Dependencies

30. **All Python dependencies are pinned in `requirements.txt`.** Major version upgrades require explicit review and testing.

31. **Frontend dependencies are pinned in `package-lock.json`.** The lockfile is committed.

32. **New dependencies are scrutinized for maintenance status, security history, license compatibility, and bundle size impact.**
