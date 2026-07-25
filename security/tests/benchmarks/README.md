# GSF Benchmarks

Performance benchmarks for GULA Security Framework (GSF) cryptographic
operations and authentication workflows.

## Requirements

- `pytest-benchmark` 5.2.3+

## Usage

```bash
# Run all benchmarks
pytest tests/benchmarks/ --benchmark-only --benchmark-autosave

# Run specific benchmark suite
pytest tests/benchmarks/ -k "TestAESBenchmark" --benchmark-only

# Compare with saved baseline
pytest tests/benchmarks/ --benchmark-compare --benchmark-autosave

# Run in CI mode (fail if >10% slower than baseline)
pytest tests/benchmarks/ --benchmark-compare --benchmark-compare-fail=min:10%
```

## Suites

| File | Suite | Measures |
|------|-------|----------|
| `test_crypto_benchmark.py` | AES-256-GCM | Encrypt/decrypt throughput (1 MiB, 10 MiB, small) |
| | Argon2id | Hash + verify latency |
| | Ed25519 | Sign + verify latency |
| | HMAC-SHA256 | Generate + verify throughput |
| | SHA-256 | Hash throughput (1 MiB) |
| | SecureRandom | Random byte/string generation |
| `test_auth_benchmark.py` | JWT | Create + verify latency (with/without claims) |
| | RBAC | Permission check latency (large roleset) |
| | Audit | Create + query + export throughput |
| | Immutable Log | Append throughput |

## Interpreting Results

- **Encryption**: aim for <1ms per 1 MiB (AES-GCM with hardware acceleration)
- **Argon2id**: target 200–500 ms (safety threshold dependent)
- **JWT**: <5 ms create, <2 ms verify
- **RBAC**: <1 ms per check with 100+ roles
- **Audit**: <0.5 ms per event append
