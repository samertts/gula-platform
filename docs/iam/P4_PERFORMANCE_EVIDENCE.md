# P4 Performance Evidence

**Current status:** `PERFORMANCE_EVIDENCE_REQUIRED`

No reproducible P50/P95/P99 benchmark suite for login, registration, workspace resolution, membership lookup, authorization, or verification lookup was found and no benchmark numbers are being invented.

## Safe static inspection scope

The remediation review must inspect authorization query paths for N+1 behavior, unbounded list queries, missing tenant/scope indexes, recursive organization traversal and authorization decision explosion. Any optimization must preserve validation, server-side authorization, audit, version checks and clinical data integrity.

## Required benchmark contract

A future non-production benchmark must use synthetic isolated data and record commit SHA, database engine/version, dataset cardinality, concurrency, cache state, query count, P50/P95/P99, error rate and audit/authorization overhead. It must cover both permitted and denied requests and must not use production data.

## Current disposition

This row is not closed by source inspection. No production performance claim is made, and no optimization that bypasses security or audit is authorized. The row remains `D`/evidence-required for P4 closure until a reproducible benchmark harness is available and reviewed.
