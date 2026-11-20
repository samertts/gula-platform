# GULA-GULS-021 Documentation Index

Program: GULA-GULS-021 — correction and verification pass on the GULS-020 foundation
Branch: `execution/gula-guls-021` in `/tmp/opencode/gula-guls-021`
Base: PR #308 head `8097a55849769c4f17e0cc731da1c180e5bc9305`; `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Date: 2026-11-21
Status: **NOT READY — BLOCKED**

## Authoritative gate document

`FINAL_ACCEPTANCE_REPORT.md` is the authoritative gate document for GULA-GULS-021. It records scope, corrections, exact verification commands/exit codes/counts, blockers, preservation evidence, and the final decision. Where any other document appears to differ, that report controls the outcome.

The final decision is **NOT READY — BLOCKED**. No Draft PR was opened because the coherent gates did not pass. No merge, deployment, production access, production key use, or human approval is claimed.

## Phase documents P00–P11

| Phase | Document                                                                                 | Subject                                                                                                            |
| ----- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| P00   | [P00_INDEPENDENT_REVIEW.md](P00_INDEPENDENT_REVIEW.md)                                   | Independent review of Draft PR #308; findings C1, H1–H4, M1–M9 and correction disposition                          |
| P01   | [P01_BACKEND_CORE_REVIEW.md](P01_BACKEND_CORE_REVIEW.md)                                 | Corrected backend core: registry, runtime, pack schema/builder/manager, delivery, preferences, clinical governance |
| P02   | [P02_WEB_OFFLINE_RUNTIME.md](P02_WEB_OFFLINE_RUNTIME.md)                                 | Web offline module: tokenized download, verification, IndexedDB activation/rollback, cache boundaries              |
| P03   | [P03_ANDROID_PLATFORM_REVIEW.md](P03_ANDROID_PLATFORM_REVIEW.md)                         | Android inventory, absent GULS integration, and native build/toolchain gap                                         |
| P04   | [P04_LANGUAGE_STANDARDS_AND_REGISTRY.md](P04_LANGUAGE_STANDARDS_AND_REGISTRY.md)         | Turkmen, Syriac, Sorani, Kurmanji, ISO/BCP 47/CLDR research and registry implications                              |
| P05   | [P05_IOS_PLATFORM_REVIEW.md](P05_IOS_PLATFORM_REVIEW.md)                                 | iOS inventory, missing buildable project metadata, and GULS integration gap                                        |
| P06   | [P06_DESKTOP_PLATFORM_REVIEW.md](P06_DESKTOP_PLATFORM_REVIEW.md)                         | Flutter/desktop and adjacent-client inventory; packaging/toolchain gaps                                            |
| P07   | [P07_DELIVERY_PREFERENCES_CLINICAL_GATES.md](P07_DELIVERY_PREFERENCES_CLINICAL_GATES.md) | Signed delivery, stable error codes, preference isolation, synthetic-pack controls, clinical/approval gates        |
| P08   | [P08_I18N_RTL_AND_FONTS.md](P08_I18N_RTL_AND_FONTS.md)                                   | i18n/RTL behavior, locale mapping, and unresolved font/license verification                                        |
| P09   | [P09_DATABASE_SECURITY_AND_CI.md](P09_DATABASE_SECURITY_AND_CI.md)                       | No-migration decision, preference reuse, secret scan, PR #308 CI red state and baseline comparison                 |
| P10   | [P10_OPERATIONAL_READINESS.md](P10_OPERATIONAL_READINESS.md)                             | Operational evidence summary and readiness conclusion                                                              |
| P11   | [P11_GATE_DECISION.md](P11_GATE_DECISION.md)                                             | Gate matrix, decision rule, final status, and re-entry criteria                                                    |

## Five mandatory evidence reports

| Report | Document                                                   | Purpose                                                                                                                    |
| ------ | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 1      | [TEST_EVIDENCE.md](TEST_EVIDENCE.md)                       | Authoritative exact-command register: commands, working directories, exit codes, test counts, and logs                     |
| 2      | [SECURITY_EVIDENCE.md](SECURITY_EVIDENCE.md)               | Threat/mitigation/evidence register for signing, archives, delivery tokens, clinical gates, and error contract             |
| 3      | [PLATFORM_COVERAGE_MATRIX.md](PLATFORM_COVERAGE_MATRIX.md) | Cross-surface coverage of Web, Android, iOS, desktop, adjacent clients, backend, and shared registry                       |
| 4      | [BLOCKERS_AND_RISKS.md](BLOCKERS_AND_RISKS.md)             | Complete open blocker and residual-risk register with evidence and exit criteria                                           |
| 5      | [ROLLBACK_AND_RECOVERY.md](ROLLBACK_AND_RECOVERY.md)       | Backend atomic install/rollback, state machine recovery, Web IndexedDB recovery, cache invalidation, preservation, caveats |

## Gate and decision

| Document                                                     | Role                                                                                                              |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| [FINAL_ACCEPTANCE_REPORT.md](FINAL_ACCEPTANCE_REPORT.md)     | Authoritative gate decision; final status **NOT READY — BLOCKED**; explicit statement that no Draft PR was opened |
| [P11_GATE_DECISION.md](P11_GATE_DECISION.md)                 | Gate-by-gate pass/fail logic and re-entry criteria                                                                |
| [P10_OPERATIONAL_READINESS.md](P10_OPERATIONAL_READINESS.md) | Operational evidence summary without full command duplication                                                     |

## Underlying evidence

Raw logs and the internal brief are outside the repository at `/tmp/opencode/gula-guls-021-evidence/`:

- `CONTEXT.md` — internal evidence brief.
- `summary.txt`, `runner.out`, `run_checks.sh` — exit-code summary and command definitions.
- Backend logs: `backend_pytest_py312.log`, `backend_pytest_py311.log`, `backend_py_compile_touched_py311.log`, `ruff_check_touched.log`, `ruff_format_check_touched.log`.
- Registry logs: `registry_schema.log`, `registry_schema_rerun.log`.
- Frontend logs: `frontend_typecheck.log`, `frontend_lint.log`, `frontend_prettier_check.log`, `frontend_focused_tests.log`, `frontend_full_tests.log`, `frontend_full_tests_baseline.log`, `frontend_build.log`.
- Repository/PR/preservation logs: `env_head.log`, `protected_workspace.log`, `pr308.log`, `pr308_checks.log`, `pr307.log`, `remote_main.log`, `changed_files.log`, `secret_scan.log`, `secret_scan_untracked_clean.log`, `local_toolchain.log`.

## Reading order

1. Start with `FINAL_ACCEPTANCE_REPORT.md` for scope, evidence, and decision.
2. Use `P11_GATE_DECISION.md` for gate logic and `P10_OPERATIONAL_READINESS.md` for the operational summary.
3. Use `BLOCKERS_AND_RISKS.md` for open items and `ROLLBACK_AND_RECOVERY.md` for recovery boundaries.
4. Consult the phase documents P00–P09 for detailed analysis and the five evidence reports for exact supporting records.

All documents in this index are in English and carry the status **NOT READY — BLOCKED**. No document in this directory grants or records approval to merge, deploy, or claim national readiness.
