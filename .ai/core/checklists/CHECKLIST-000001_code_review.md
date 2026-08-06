---
id: CHECKLIST-000001
type: checklist
title: "Code Review Checklist"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [review, checklist, quality, code]
---

# Code Review Checklist

Use this checklist for every code review. All items must pass.

## Correctness
- [ ] Code compiles/builds without errors
- [ ] All tests pass
- [ ] Logic is correct for stated requirements
- [ ] Edge cases handled
- [ ] Error handling present and appropriate

## Security
- [ ] No secrets or credentials in code
- [ ] Input validation present
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] Authentication/authorization checks
- [ ] No hardcoded URLs with credentials
- [ ] OWASP Top 10 considered

## Architecture
- [ ] Follows Clean Architecture / SOLID principles
- [ ] No circular dependencies
- [ ] Proper layer separation (route → service → model)
- [ ] No vendor lock-in introduced
- [ ] Meets constitution requirements (Free First, Open Source First)

## Code Quality
- [ ] No dead code
- [ ] No commented-out code
- [ ] Functions are single-purpose
- [ ] No duplicated logic
- [ ] Meaningful variable/function names
- [ ] Type hints present (Python)
- [ ] No magic numbers

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added if needed
- [ ] Test coverage adequate
- [ ] Tests are deterministic (no flakiness)
- [ ] Edge cases tested

## Performance
- [ ] No N+1 queries
- [ ] Proper indexing considered
- [ ] Caching used where appropriate
- [ ] No unnecessary DB calls
- [ ] Async used for I/O operations

## Documentation
- [ ] Public functions have docstrings
- [ ] Complex logic has comments
- [ ] README updated if needed
- [ ] API docs updated if endpoints changed
- [ ] ADR created for architectural decisions

## Compatibility
- [ ] Backward compatible (no breaking changes)
- [ ] Database migration is reversible
- [ ] API versioning maintained
- [ ] Frontend-backend contract maintained

## Constitution Compliance
- [ ] Free First: no paid dependencies added
- [ ] Open Source First: license compatible
- [ ] Self-Hosted First: no SaaS-only features
- [ ] No Vendor Lock-In: components replaceable
- [ ] Zero Paid Dependency: cost analysis if needed
