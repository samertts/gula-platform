# GULA Testing Constitution

## Testing Philosophy

Testing is not a phase. Testing is an integral part of development. Every line of code is tested at the appropriate level. Tests provide confidence, documentation, and safety nets for refactoring.

## Test Pyramid

1. **Unit tests** (70% of test effort) — Test individual functions, service methods, and utility code in isolation. Dependencies are mocked.

2. **Integration tests** (20% of test effort) — Test API endpoints, database interactions, and inter-service communication with real or containerized dependencies.

3. **End-to-end tests** (10% of test effort) — Test critical user journeys through the full stack (frontend + backend + database).

## Requirements

4. **Every service method must have at least one unit test.** Business logic in services is the primary testing target.

5. **Every API endpoint must have at least one integration test** that verifies the happy path and at least two error conditions.

6. **Every database migration must be round-trip tested:** `upgrade` → `downgrade -1` → `upgrade head`.

7. **Clinical decision support rules** have dedicated tests for each rule with known inputs and expected outputs.

8. **State machines** have tests for every state transition, including invalid transitions.

## Test Quality

9. **Tests must be deterministic.** Flaky tests are treated as bugs. A flaky test is disabled only after investigation and documentation.

10. **Tests should not depend on external services** unless explicitly labeled as integration tests. External service tests use Testcontainers or similar.

11. **Test data is explicit.** Tests create their own data rather than depending on shared fixtures.

12. **Tests clean up after themselves.** Test databases are reset between runs.

## Coverage

13. **Minimum 80% line coverage** for service modules. 90% for domain logic (state machines, validation rules). See Article 28 (Definition of Done) for quality gate criteria.

14. **Coverage is measured per module**, not globally. A module with low coverage blocks the build.

15. **Coverage requirements are enforced in CI.** Coverage reports are published. Exceptions require ADR approval (see Article 27).

## Test Automation

16. **Tests run automatically on every push** in CI.

17. **Tests must complete within 10 minutes** for the entire backend test suite.

18. **Slow tests are tagged** with `@pytest.mark.slow` and run less frequently (nightly, pre-release).

## Testing Standards

19. **Assertions over print debugging.** Every test must have at least one assert.

20. **Arrange-Act-Assert** pattern is followed consistently.

21. **Mock external APIs** at the service boundary, not the HTTP layer.

22. **Test error messages.** Verify that error responses contain expected codes and messages.

23. **Test Arabic content.** Verify that Arabic translations are present and correctly formatted for RTL.
