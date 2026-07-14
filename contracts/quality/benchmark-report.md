# GULA Platform Performance Benchmark Report

**Generated:** 2026-07-14T14:32:44.254208Z
**Targets:** P95 < 150ms, P99 < 300ms
**Overall Status:** FAIL

---

## Methodology

All benchmarks are run in-process using mocked dependencies (DBMock, CacheMock) to isolate serialization and logic performance from network variance. Each benchmark executes:

- **Warmup rounds:** 10 (discarded)
- **Measured rounds:** 100 per test (fewer for expensive tests)
- **Concurrency levels tested:** [1, 10, 25, 50]

Timings are collected via `time.perf_counter()` with nanosecond precision. Percentiles (P50, P95, P99) are computed from the sorted timing distribution.

---

## Results Summary

| Benchmark | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Status |
|-----------|-----------|----------|----------|----------|--------|
| rest_api_serialization_small | 0.01 | 0.01 | 0.01 | 0.01 | ✅ PASS |
| rest_api_serialization_medium | 0.06 | 0.05 | 0.10 | 0.24 | ✅ PASS |
| rest_api_serialization_large | 0.33 | 0.21 | 0.87 | 3.31 | ✅ PASS |
| rest_api_response_render_small | 0.00 | 0.00 | 0.00 | 0.01 | ✅ PASS |
| rest_api_response_render_medium | 0.11 | 0.11 | 0.15 | 0.23 | ✅ PASS |
| rest_api_response_render_large | 2.74 | 1.85 | 8.51 | 16.35 | ✅ PASS |
| fhir_patient_serialize | 0.03 | 0.02 | 0.04 | 0.11 | ✅ PASS |
| fhir_observation_serialize | 0.02 | 0.02 | 0.02 | 0.14 | ✅ PASS |
| fhir_diagnostic_report_serialize | 0.02 | 0.01 | 0.02 | 0.08 | ✅ PASS |
| fhir_bundle_serialize | 0.05 | 0.04 | 0.07 | 0.11 | ✅ PASS |
| fhir_patient_roundtrip | 0.05 | 0.04 | 0.10 | 0.34 | ✅ PASS |
| event_lims_result_created_serialize | 0.01 | 0.01 | 0.01 | 0.01 | ✅ PASS |
| event_lims_result_created_deserialize | 0.01 | 0.01 | 0.01 | 0.01 | ✅ PASS |
| event_all_types_bulk_roundtrip | 0.31 | 0.34 | 0.43 | 0.45 | ✅ PASS |
| dto_patient_roundtrip | 0.03 | 0.02 | 0.05 | 0.17 | ✅ PASS |
| dto_order_roundtrip | 0.02 | 0.02 | 0.02 | 0.02 | ✅ PASS |
| dto_result_roundtrip | 0.01 | 0.01 | 0.01 | 0.04 | ✅ PASS |
| dto_catalog_all_serialize | 2.40 | 1.61 | 5.83 | 7.42 | ✅ PASS |
| db_query_1_rows | 5.76 | 5.34 | 9.22 | 10.04 | ✅ PASS |
| db_query_10_rows | 5.68 | 5.37 | 7.26 | 8.91 | ✅ PASS |
| db_query_100_rows | 5.96 | 5.40 | 9.44 | 10.44 | ✅ PASS |
| db_query_1000_rows | 6.92 | 5.95 | 10.52 | 10.58 | ✅ PASS |
| db_batch_1_queries | 5.64 | 5.35 | 7.65 | 9.50 | ✅ PASS |
| db_batch_5_queries | 28.95 | 27.68 | 34.97 | 35.26 | ✅ PASS |
| db_batch_20_queries | 116.81 | 115.89 | 128.35 | 133.47 | ✅ PASS |
| db_complex_join_pattern | 11.78 | 11.10 | 15.27 | 16.24 | ✅ PASS |
| db_latency_1ms | 2.54 | 1.32 | 5.33 | 22.21 | ✅ PASS |
| db_latency_5ms | 5.84 | 5.42 | 8.84 | 10.51 | ✅ PASS |
| db_latency_20ms | 20.98 | 20.48 | 24.09 | 25.26 | ✅ PASS |
| db_latency_50ms | 51.26 | 50.52 | 55.12 | 58.44 | ✅ PASS |
| cache_get_hit | 1.76 | 1.33 | 4.96 | 8.40 | ✅ PASS |
| cache_get_miss | 1.85 | 1.33 | 5.31 | 12.87 | ✅ PASS |
| cache_set | 2.98 | 2.46 | 6.27 | 7.64 | ✅ PASS |
| cache_set_64b | 2.83 | 2.47 | 5.57 | 6.48 | ✅ PASS |
| cache_set_1024b | 2.90 | 2.48 | 6.83 | 7.89 | ✅ PASS |
| cache_set_10240b | 3.26 | 2.49 | 7.47 | 10.27 | ✅ PASS |
| cache_set_102400b | 2.93 | 2.47 | 6.29 | 6.94 | ✅ PASS |
| cache_mget_50_keys | 81.25 | 80.92 | 96.22 | 100.63 | ✅ PASS |
| cache_mset_20_keys | 66.77 | 60.71 | 124.78 | 159.80 | ✅ PASS |
| cache_delete | 4.63 | 3.74 | 9.02 | 11.70 | ✅ PASS |
| sync_batch_process_10 | 0.10 | 0.10 | 0.10 | 0.18 | ✅ PASS |
| sync_batch_process_50 | 0.53 | 0.27 | 3.13 | 4.46 | ✅ PASS |
| sync_batch_process_200 | 2.95 | 1.80 | 8.32 | 9.40 | ✅ PASS |
| sync_conflict_resolution_50 | 0.13 | 0.02 | 0.03 | 3.40 | ✅ PASS |
| sync_payload_compact_serialize | 4.51 | 5.35 | 8.98 | 8.98 | ✅ PASS |
| concurrent_db_1 | 6.20 | 5.57 | 10.46 | 10.46 | ✅ PASS |
| concurrent_db_10 | 6.99 | 6.71 | 11.24 | 11.24 | ✅ PASS |
| concurrent_db_25 | 8.09 | 7.96 | 13.07 | 13.07 | ✅ PASS |
| concurrent_db_50 | 8.43 | 7.34 | 17.79 | 17.79 | ✅ PASS |
| concurrent_cache_1 | 4.92 | 4.16 | 8.61 | 8.61 | ✅ PASS |
| concurrent_cache_10 | 6.14 | 5.11 | 10.11 | 10.11 | ✅ PASS |
| concurrent_cache_25 | 7.41 | 7.58 | 11.23 | 11.23 | ✅ PASS |
| concurrent_cache_50 | 10.45 | 9.89 | 16.78 | 16.78 | ✅ PASS |
| concurrent_fhir_serialize_1 | 0.11 | 0.11 | 0.24 | 0.24 | ✅ PASS |
| concurrent_fhir_serialize_10 | 0.50 | 0.41 | 1.05 | 1.05 | ✅ PASS |
| concurrent_fhir_serialize_25 | 1.16 | 1.25 | 2.02 | 2.02 | ✅ PASS |
| concurrent_fhir_serialize_50 | 1.60 | 1.61 | 2.48 | 2.48 | ✅ PASS |
| mixed_workload_25_concurrent | 15.20 | 14.34 | 20.46 | 20.46 | ✅ PASS |
| n_plus_one_naive_100 | 605.09 | 604.95 | 645.38 | 645.38 | ❌ FAIL |
| n_plus_one_batched_100_b20 | 628.01 | 622.93 | 719.13 | 719.13 | ❌ FAIL |
| n_plus_one_optimized_100 | 6.16 | 5.52 | 10.91 | 10.91 | ✅ PASS |
| n_plus_one_naive_10 | 60.78 | 60.09 | 69.44 | 69.44 | ✅ PASS |
| n_plus_one_batched_10 | 64.39 | 63.24 | 72.54 | 72.54 | ✅ PASS |
| n_plus_one_naive_50 | 305.35 | 305.18 | 320.42 | 320.42 | ❌ FAIL |
| n_plus_one_batched_50 | 286.49 | 286.91 | 302.54 | 302.54 | ❌ FAIL |
| n_plus_one_naive_100 | 585.32 | 583.03 | 641.79 | 641.79 | ❌ FAIL |
| n_plus_one_batched_100 | 600.28 | 598.78 | 629.99 | 629.99 | ❌ FAIL |

**Passed:** 61 | **Warnings:** 0 | **Failed:** 6

---

## Detailed Results by Category

### REST API Throughput

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| rest_api_serialization_small | 0.006 | 0.006 | 0.007 | 0.006 | 0.007 | 0.007 | 0.000 | ✅ PASS |
| rest_api_serialization_medium | 0.056 | 0.029 | 0.243 | 0.053 | 0.099 | 0.243 | 0.031 | ✅ PASS |
| rest_api_serialization_large | 0.327 | 0.203 | 3.305 | 0.210 | 0.874 | 3.305 | 0.465 | ✅ PASS |
| rest_api_response_render_small | 0.004 | 0.004 | 0.005 | 0.004 | 0.004 | 0.005 | 0.000 | ✅ PASS |
| rest_api_response_render_medium | 0.112 | 0.104 | 0.227 | 0.107 | 0.148 | 0.227 | 0.020 | ✅ PASS |
| rest_api_response_render_large | 2.743 | 1.417 | 16.346 | 1.850 | 8.506 | 16.346 | 2.704 | ✅ PASS |

### FHIR Resource Serialization

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| fhir_patient_serialize | 0.025 | 0.021 | 0.107 | 0.021 | 0.043 | 0.107 | 0.013 | ✅ PASS |
| fhir_observation_serialize | 0.020 | 0.017 | 0.141 | 0.018 | 0.019 | 0.141 | 0.013 | ✅ PASS |
| fhir_diagnostic_report_serialize | 0.017 | 0.015 | 0.077 | 0.015 | 0.023 | 0.077 | 0.008 | ✅ PASS |
| fhir_bundle_serialize | 0.047 | 0.040 | 0.112 | 0.041 | 0.072 | 0.112 | 0.012 | ✅ PASS |
| fhir_patient_roundtrip | 0.048 | 0.036 | 0.336 | 0.040 | 0.103 | 0.336 | 0.034 | ✅ PASS |

### Event Serialization

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| event_lims_result_created_serialize | 0.009 | 0.008 | 0.011 | 0.008 | 0.009 | 0.011 | 0.000 | ✅ PASS |
| event_lims_result_created_deserialize | 0.007 | 0.006 | 0.012 | 0.007 | 0.011 | 0.012 | 0.001 | ✅ PASS |
| event_all_types_bulk_roundtrip | 0.307 | 0.190 | 0.450 | 0.337 | 0.429 | 0.450 | 0.081 | ✅ PASS |

### DTO Serialization

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| dto_patient_roundtrip | 0.025 | 0.017 | 0.168 | 0.020 | 0.049 | 0.168 | 0.017 | ✅ PASS |
| dto_order_roundtrip | 0.019 | 0.019 | 0.021 | 0.019 | 0.020 | 0.021 | 0.000 | ✅ PASS |
| dto_result_roundtrip | 0.012 | 0.011 | 0.037 | 0.011 | 0.015 | 0.037 | 0.004 | ✅ PASS |
| dto_catalog_all_serialize | 2.397 | 1.311 | 7.424 | 1.613 | 5.826 | 7.424 | 1.649 | ✅ PASS |

### Database Queries

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| db_query_1_rows | 5.761 | 5.254 | 10.037 | 5.336 | 9.223 | 10.037 | 1.219 | ✅ PASS |
| db_query_10_rows | 5.683 | 5.247 | 8.913 | 5.369 | 7.258 | 8.913 | 0.785 | ✅ PASS |
| db_query_100_rows | 5.962 | 5.255 | 10.440 | 5.397 | 9.439 | 10.440 | 1.275 | ✅ PASS |
| db_query_1000_rows | 6.916 | 5.509 | 10.584 | 5.946 | 10.522 | 10.584 | 1.578 | ✅ PASS |
| db_batch_1_queries | 5.642 | 5.269 | 9.502 | 5.348 | 7.654 | 9.502 | 0.863 | ✅ PASS |
| db_batch_5_queries | 28.947 | 26.499 | 35.260 | 27.675 | 34.965 | 35.260 | 2.644 | ✅ PASS |
| db_batch_20_queries | 116.806 | 108.521 | 133.468 | 115.894 | 128.348 | 133.468 | 5.224 | ✅ PASS |
| db_complex_join_pattern | 11.781 | 10.650 | 16.244 | 11.102 | 15.268 | 16.244 | 1.503 | ✅ PASS |
| db_latency_1ms | 2.544 | 1.204 | 22.206 | 1.325 | 5.326 | 22.206 | 3.866 | ✅ PASS |
| db_latency_5ms | 5.845 | 5.254 | 10.508 | 5.425 | 8.838 | 10.508 | 1.174 | ✅ PASS |
| db_latency_20ms | 20.980 | 20.244 | 25.262 | 20.482 | 24.085 | 25.262 | 1.203 | ✅ PASS |
| db_latency_50ms | 51.257 | 50.299 | 58.443 | 50.522 | 55.120 | 58.443 | 1.874 | ✅ PASS |

### Cache Operations

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| cache_get_hit | 1.758 | 1.199 | 8.397 | 1.332 | 4.957 | 8.397 | 1.315 | ✅ PASS |
| cache_get_miss | 1.849 | 1.218 | 12.865 | 1.327 | 5.313 | 12.865 | 1.589 | ✅ PASS |
| cache_set | 2.985 | 2.280 | 7.645 | 2.457 | 6.266 | 7.645 | 1.268 | ✅ PASS |
| cache_set_64b | 2.825 | 2.330 | 6.476 | 2.474 | 5.567 | 6.476 | 1.036 | ✅ PASS |
| cache_set_1024b | 2.898 | 2.272 | 7.893 | 2.483 | 6.835 | 7.893 | 1.250 | ✅ PASS |
| cache_set_10240b | 3.257 | 2.295 | 10.270 | 2.486 | 7.470 | 10.270 | 1.935 | ✅ PASS |
| cache_set_102400b | 2.928 | 2.342 | 6.940 | 2.473 | 6.285 | 6.940 | 1.177 | ✅ PASS |
| cache_mget_50_keys | 81.250 | 68.567 | 100.629 | 80.924 | 96.216 | 100.629 | 8.164 | ✅ PASS |
| cache_mset_20_keys | 66.773 | 46.851 | 159.803 | 60.714 | 124.784 | 159.803 | 23.456 | ✅ PASS |
| cache_delete | 4.633 | 3.405 | 11.697 | 3.744 | 9.018 | 11.697 | 1.848 | ✅ PASS |

### Offline Sync Processing

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| sync_batch_process_10 | 0.098 | 0.079 | 0.181 | 0.098 | 0.103 | 0.181 | 0.017 | ✅ PASS |
| sync_batch_process_50 | 0.526 | 0.241 | 4.462 | 0.266 | 3.133 | 4.462 | 0.895 | ✅ PASS |
| sync_batch_process_200 | 2.952 | 0.952 | 9.399 | 1.798 | 8.320 | 9.399 | 2.555 | ✅ PASS |
| sync_conflict_resolution_50 | 0.134 | 0.013 | 3.396 | 0.024 | 0.029 | 3.396 | 0.606 | ✅ PASS |
| sync_payload_compact_serialize | 4.506 | 1.241 | 8.980 | 5.354 | 8.980 | 8.980 | 2.657 | ✅ PASS |

### Concurrent Request Handling

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| concurrent_db_1 | 6.204 | 5.416 | 10.455 | 5.571 | 10.455 | 10.455 | 1.523 | ✅ PASS |
| concurrent_db_10 | 6.985 | 5.706 | 11.242 | 6.706 | 11.242 | 11.242 | 1.345 | ✅ PASS |
| concurrent_db_25 | 8.092 | 5.964 | 13.070 | 7.960 | 13.070 | 13.070 | 1.747 | ✅ PASS |
| concurrent_db_50 | 8.434 | 6.359 | 17.791 | 7.345 | 17.791 | 17.791 | 2.734 | ✅ PASS |
| concurrent_cache_1 | 4.922 | 3.797 | 8.613 | 4.160 | 8.613 | 8.613 | 1.614 | ✅ PASS |
| concurrent_cache_10 | 6.138 | 4.436 | 10.110 | 5.106 | 10.110 | 10.110 | 1.933 | ✅ PASS |
| concurrent_cache_25 | 7.409 | 5.027 | 11.229 | 7.580 | 11.229 | 11.229 | 2.000 | ✅ PASS |
| concurrent_cache_50 | 10.454 | 6.405 | 16.782 | 9.894 | 16.782 | 16.782 | 2.980 | ✅ PASS |
| concurrent_fhir_serialize_1 | 0.106 | 0.043 | 0.242 | 0.106 | 0.242 | 0.242 | 0.055 | ✅ PASS |
| concurrent_fhir_serialize_10 | 0.496 | 0.405 | 1.054 | 0.411 | 1.054 | 1.054 | 0.177 | ✅ PASS |
| concurrent_fhir_serialize_25 | 1.164 | 0.552 | 2.022 | 1.253 | 2.022 | 2.022 | 0.352 | ✅ PASS |
| concurrent_fhir_serialize_50 | 1.596 | 1.050 | 2.475 | 1.609 | 2.475 | 2.475 | 0.496 | ✅ PASS |
| mixed_workload_25_concurrent | 15.198 | 13.282 | 20.458 | 14.342 | 20.458 | 20.458 | 2.008 | ✅ PASS |

### N+1 Query Detection

| Benchmark | Mean (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Stddev | Status |
|-----------|-----------|----------|----------|----------|----------|----------|--------|--------|
| n_plus_one_naive_100 | 605.087 | 585.966 | 645.376 | 604.946 | 645.376 | 645.376 | 15.074 | ❌ FAIL |
| n_plus_one_batched_100_b20 | 628.015 | 588.451 | 719.135 | 622.933 | 719.135 | 719.135 | 39.726 | ❌ FAIL |
| n_plus_one_optimized_100 | 6.155 | 5.353 | 10.907 | 5.518 | 10.907 | 10.907 | 1.627 | ✅ PASS |
| n_plus_one_naive_10 | 60.785 | 57.440 | 69.438 | 60.091 | 69.438 | 69.438 | 3.387 | ✅ PASS |
| n_plus_one_batched_10 | 64.394 | 58.759 | 72.543 | 63.236 | 72.543 | 72.543 | 3.854 | ✅ PASS |
| n_plus_one_naive_50 | 305.354 | 291.860 | 320.417 | 305.181 | 320.417 | 320.417 | 9.715 | ❌ FAIL |
| n_plus_one_batched_50 | 286.485 | 277.724 | 302.539 | 286.910 | 302.539 | 302.539 | 6.803 | ❌ FAIL |
| n_plus_one_naive_100 | 585.318 | 563.864 | 641.788 | 583.031 | 641.788 | 641.788 | 21.503 | ❌ FAIL |
| n_plus_one_batched_100 | 600.279 | 580.146 | 629.994 | 598.777 | 629.994 | 629.994 | 16.508 | ❌ FAIL |

---

## Comparison Against Targets

Target P95: **< 150ms**
Target P99: **< 300ms**

| Metric | Count |
|--------|-------|
| Benchmarks meeting P95 target | 61/67 (91.0%) |
| Benchmarks meeting P99 target | 61/67 (91.0%) |

#### P95 Exceedances
- **n_plus_one_naive_100**: 645.38ms (target: 150ms)
- **n_plus_one_batched_100_b20**: 719.13ms (target: 150ms)
- **n_plus_one_naive_50**: 320.42ms (target: 150ms)
- **n_plus_one_batched_50**: 302.54ms (target: 150ms)
- **n_plus_one_naive_100**: 641.79ms (target: 150ms)
- **n_plus_one_batched_100**: 629.99ms (target: 150ms)

#### P99 Exceedances
- **n_plus_one_naive_100**: 645.38ms (target: 300ms)
- **n_plus_one_batched_100_b20**: 719.13ms (target: 300ms)
- **n_plus_one_naive_50**: 320.42ms (target: 300ms)
- **n_plus_one_batched_50**: 302.54ms (target: 300ms)
- **n_plus_one_naive_100**: 641.79ms (target: 300ms)
- **n_plus_one_batched_100**: 629.99ms (target: 300ms)

---

## N+1 Query Analysis

The N+1 query pattern occurs when an application executes one query to fetch parent entities and then N additional queries to fetch related child entities. This is a common performance anti-pattern in ORM-based applications.

| Pattern | Iterations | Mean (ms) | Total Time (ms) | vs Optimized |
|---------|-----------|-----------|----------------|--------------|
| Naive (N=100) | 100 | 605.087 | 60508.700 | 98.3x slower (batched: 1.0x slower) |
| Naive (N=10) | 10 | 60.785 | 607.850 | N/A (batched: 0.9x slower) |
| Naive (N=50) | 50 | 305.354 | 15267.700 | N/A (batched: 1.1x slower) |
| Naive (N=100) | 100 | 585.318 | 58531.800 | 95.1x slower (batched: 1.0x slower) |
| Batched (N=20) | 20 | 628.015 | 1884.045 | N/A |
| Batched (N=10) | 10 | 64.394 | 128.788 | N/A |
| Batched (N=50) | 50 | 286.485 | 1718.910 | N/A |
| Batched (N=100) | 100 | 600.279 | 6603.069 | 97.5x slower |
| Optimized JOIN (N=100) | 100 | 6.155 | 6.155 | 1x (baseline) |

**Recommendation:** Use batched queries or JOINs instead of N+1 loop patterns. The batched approach reduces DB round-trips from N to N/batch_size, while JOINs eliminate round-trips entirely for related data.

---

## Connection Pooling Validation

The database connection pool is configured with: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections`.

Current configuration validates:
- Default pool size: 6 connections per worker
- Max overflow: 12 connections per worker
- Workers: 3 (gunicorn)
- Budget: 3 × (6 + 12) = 54 connections (within Postgres default of 100)

Concurrent benchmarks above verify that the pool can handle simultaneous requests without starvation. The mixed workload test with 25 concurrent operations (DB + cache + serialize) validates that connection acquisition does not become a bottleneck.

| Concurrency Level | Mean (ms) | P95 (ms) | Status |
|-------------------|-----------|----------|--------|
| 1 concurrent | 6.204 | 10.455 | ✅ PASS |
| 10 concurrent | 6.985 | 11.242 | ✅ PASS |
| 25 concurrent | 8.092 | 13.070 | ✅ PASS |
| 50 concurrent | 8.434 | 17.791 | ✅ PASS |

---

## Caching Validation

Cache operations are benchmarked with mock Redis latency (1ms get, 2ms set). The following validations are performed:

- **Cache hit latency:** Expected < 5ms for key retrieval
- **Cache miss latency:** Expected < 5ms for miss detection
- **Cache write latency:** Expected < 10ms for value storage
- **Bulk operations:** MGET/MSET with 20-50 keys
- **Value size impact:** Tested at 64B, 1KB, 10KB, 100KB

| Operation | Mean (ms) | P95 (ms) | P99 (ms) | Status |
|-----------|-----------|----------|----------|--------|
| cache_get_hit | 1.758 | 4.957 | 8.397 | ✅ PASS |
| cache_get_miss | 1.849 | 5.313 | 12.865 | ✅ PASS |
| cache_set | 2.985 | 6.266 | 7.645 | ✅ PASS |
| cache_set_64b | 2.825 | 5.567 | 6.476 | ✅ PASS |
| cache_set_1024b | 2.898 | 6.835 | 7.893 | ✅ PASS |
| cache_set_10240b | 3.257 | 7.470 | 10.270 | ✅ PASS |
| cache_set_102400b | 2.928 | 6.285 | 6.940 | ✅ PASS |
| cache_mget_50_keys | 81.250 | 96.216 | 100.629 | ✅ PASS |
| cache_mset_20_keys | 66.773 | 124.784 | 159.803 | ✅ PASS |
| cache_delete | 4.633 | 9.018 | 11.697 | ✅ PASS |

**Cache hit ratio recommendation:**
- Target cache hit ratio: > 90% for frequently accessed patient/result data
- Use `cache_get_miss` benchmark as baseline for miss penalty
- For values > 10KB, consider compression or alternative storage
- Bulk MGET should be preferred over sequential GET for batch operations

---

## Recommendations

### Critical Issues

- **n_plus_one_naive_100**: 645.38ms P95 (target: 150ms) / 645.38ms P99 (target: 300ms). Investigate serialization overhead and consider streaming responses.
- **n_plus_one_batched_100_b20**: 719.13ms P95 (target: 150ms) / 719.13ms P99 (target: 300ms). Investigate serialization overhead and consider streaming responses.
- **n_plus_one_naive_50**: 320.42ms P95 (target: 150ms) / 320.42ms P99 (target: 300ms). Investigate serialization overhead and consider streaming responses.
- **n_plus_one_batched_50**: 302.54ms P95 (target: 150ms) / 302.54ms P99 (target: 300ms). Investigate serialization overhead and consider streaming responses.
- **n_plus_one_naive_100**: 641.79ms P95 (target: 150ms) / 641.79ms P99 (target: 300ms). Investigate serialization overhead and consider streaming responses.
- **n_plus_one_batched_100**: 629.99ms P95 (target: 150ms) / 629.99ms P99 (target: 300ms). Investigate serialization overhead and consider streaming responses.

### Warnings
None — all benchmarks meet P99 targets.

### Performance Improvements

1. **N+1 Query Prevention:** Always use JOINs or batched queries over loop-based fetching.
2. **FHIR Serialization:** Cache serialized FHIR resources where possible; consider using `orjson` for speed.
3. **Event Batching:** Batch event publication (MSET/MGET) rather than individual SET/GET operations.
4. **Connection Pooling:** Monitor concurrent DB benchmarks to ensure pool size is adequate at peak load.
5. **Offline Sync:** Compact sync payloads with `separators=(',', ':')` and batch conflict resolution.
6. **Cache Strategy:** Implement multi-level caching (local LRU + Redis) for hot patient/order data.
7. **Large Payloads:** For response payloads > 100KB, consider pagination or streaming.

### Monitoring

- Integrate these benchmarks into CI to catch regressions before deployment
- Set up alerting when P95 exceeds 120ms (80% of target) as early warning
- Run concurrent benchmarks weekly to detect connection pool starvation
- Track cache hit ratio in production; aim for > 90% on patient/result lookups
