# Final full backend regression — 2026-11-24

## Exact command

```bash
cd /home/samertts/workspace/projects/gula-integration-v4-execution/backend
/home/samertts/.cache/gula-int-py312/bin/python -m pytest -q \
  > /tmp/opencode/v4_full_backend_tests_final.log 2>&1
echo "EXIT=$?" >> /tmp/opencode/v4_full_backend_tests_final.log
```

## Result

| Field | Value |
| --- | --- |
| Interpreter | `/home/samertts/.cache/gula-int-py312/bin/python` |
| Python | `3.12.13` |
| pytest | `9.2.0` |
| Collected | `5,307` items |
| Passed | `5,223` |
| Skipped | `84` |
| Warnings | `213` |
| Duration | `770.27s (0:12:50)` |
| Failures / errors | `0 / 0` |
| Exit code | `0` |
| Preserved log | `AUDIT_EXECUTION_RECORDS/V4_WAVE_A_FULL_TEST_LOG_FINAL_EXECUTION_2026_11_24.txt` |
| Log SHA-256 | `411c0f1e40509d15a9ab274a63ea686f80f510e8faf38ac823a4ac0de4bd359b` |

## Classification

This run occurred after the no-silent-STUB guard, event-authority
implementation, event migration, event tests, and frontend authorization
bootstrap changes. It is therefore the final backend regression for the V4
execution workspace.

The increase from the prior post-hardening result (`5,216 passed, 80 skipped`)
is accounted for by the new event-consolidation suites. The four extra skips are
PostgreSQL/event DSN-gated tests that were executed separately:
`V4_EVENT_AUTHORITY_POSTGRES_GREEN_2026_11_24.txt` (`4 passed`),
`V4_CRUD_POSTGRES_GREEN_2026_11_24.txt`, and
`V4_GUARD_WITH_POSTGRES_GREEN_2026_11_24.txt` (`75 passed, 1 warning`).

No failure was suppressed. All 213 warnings are dependency/deprecation warnings
already present in the baseline; none is treated as a pass or a gate result.
