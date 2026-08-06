# Coding Standards

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Standalone coding standards for the GULA Platform.
Derived from PROJECT_MEMORY.md and constitution.

---

## Python Standards

| Standard | Rule |
|---|---|
| Version | 3.12 |
| Style | PEP 8 |
| Naming | snake_case (functions, variables) |
| Classes | PascalCase |
| Constants | UPPER_SNAKE_CASE |
| Type Hints | Mandatory on public functions |
| Docstrings | Google style |
| Imports | stdlib, third-party, local |
| Max Line | 88 characters |
| Linter | Ruff |
| Type Checker | mypy |

---

## TypeScript Standards

| Standard | Rule |
|---|---|
| Style | Strict mode |
| Naming | camelCase (functions, variables) |
| Classes | PascalCase |
| Interfaces | PascalCase with I prefix |
| Constants | UPPER_SNAKE_CASE |
| Max Line | 100 characters |
| Linter | ESLint |
| Formatter | Prettier |

---

## General Standards

| Standard | Rule |
|---|---|
| Commits | Conventional Commits |
| Messages | imperative mood |
| Scope | module name |
| Body | what and why, not how |

---

## Import Order

1. Standard library
2. Third-party packages
3. Local modules
4. Relative imports

---

## Error Handling

- Never catch bare exceptions
- Always log errors
- Always provide context
- Never suppress errors silently

---

## Testing Standards

| Standard | Rule |
|---|---|
| Framework | pytest (Python), Vitest (TypeScript) |
| Coverage | 100% for new code |
| Naming | test_[function_name] |
| Structure | Arrange, Act, Assert |
| Isolation | Each test independent |

---

## References

- `.ai/core/memory/PROJECT_MEMORY.md` — Full standards
- AI_OPERATING_CONSTITUTION.md — Section 5
- `.ai/core/quality/GOVERNANCE_RULES.md` — Governance
