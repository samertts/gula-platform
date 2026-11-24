# Wave A final post-hardening full regression — 2026-11-24

## Exact command

```bash
cd /home/samertts/workspace/projects/gula-integration-v4-execution/backend
/home/samertts/.cache/gula-int-py312/bin/python -m pytest -q \
  > /tmp/opencode/v4_full_backend_tests_after_hardening.log 2>&1
echo "EXIT=$?" >> /tmp/opencode/v4_full_backend_tests_after_hardening.log
```

## Result

| Field | Value |
| --- | --- |
| Interpreter | `/home/samertts/.cache/gula-int-py312/bin/python` |
| Python | `3.12.13` |
| pytest | `9.2.0` |
| Collected/executed summary | `5216 passed, 80 skipped, 213 warnings in 661.90s (0:11:01)` |
| Exit code | `0` |
| Failures | `0` |
| Errors | `0` |
| Skips | `80` (73 more than the pre-hardening run: PostgreSQL-only suites skip when their disposable DSNs are not exported; all were run separately with DSNs and passed) |
| Warnings | `213` (same count as the pre-hardening clean run; dependency/deprecation warnings, no warning upgraded to failure) |
| Preserved log | `AUDIT_EXECUTION_RECORDS/V4_WAVE_A_FULL_TEST_LOG_POST_HARDENING_2026_11_24.txt` |
| Log SHA-256 | `dde5d503f878a759b378022018d525b45ddf609d00cfafcb378ca73910ea91ee` |

## Classification

No failures or errors occurred. The four skipped PostgreSQL-specific suites
were not hidden failures: identical files were executed with disposable DSNs in
the same batch and produced `75 passed, 1 warning`, including CRUD/P03 chain
and cross-track tests. All remaining skips are pre-existing environment or
capability skips already present in the baseline full-suite run.

The post-hardening run includes every final code change in this batch:
capability lab ownership and audit, P-03 deferred anchor emission, contract
exact-path drift guard, expanded CI guard, and the fixed PostgreSQL harnesses.
Wave A is therefore technically closed. Owner-controlled release status is
unchanged.
