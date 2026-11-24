# Final Report 03 — FHIR R4 (WS-C) + I-2 remediation

**Report ID:** PR-FINAL-03 · **Date:** 2026-11-18 · **Data class:** SYNTHETIC ONLY
**Governing decision:** HOLD / REJECT unchanged. Development evidence only.

## 1. Classification

| Deliverable | Classification | Basis |
|---|---|---|
| FHIR R4 resource round-trip adapter (supported resources, field equality, denied-type catalogue) | **PARTIALLY VERIFIED** | 97 local adapter tests (25 outcome + 32 roundtrip + 40 validation); no HTTP/FHIR endpoint exists in the sandbox |
| `OperationOutcome` error adapter (canonical error → R4 issue code / severity / diagnostics) | **VERIFIED (local)** | Shape, valid R4 code set, severity mapping and sanitisation all strictly tested |
| Real `application/fhir+json` wire endpoint | **NOT IMPLEMENTED** | Owner-gated; no route activation |

Overall workstream classification: **PARTIALLY VERIFIED** (adapter correctness verified; wire/serving surface absent by design).

## 2. The informational finding — I-2

**Finding (`ADVERSARIAL_REVIEW_SECURITY.md` §I-2):** `operation_outcome_from_error()` appended `json.dumps(dict(error.details))` verbatim into `OperationOutcome.issue.diagnostics`. A client-supplied string such as `<script>alert(1)</script>` was echoed into `diagnostics`. It is JSON (not executable by the API), but an HTML consumer rendering `diagnostics` unescaped would have an XSS sink.

**Fix:**
- Explicit documented allowlist `_DIAGNOSTICS_ALLOWED_DETAIL_KEYS = {"field", "key", "reason", "expected", "actual", "status"}` — descriptive validation context only, chosen after auditing all `details=` call sites. Identifier-bearing keys in common use (`tenant_id`, `patient_ref`, `identifier`, `barcode`, `order_id`, other `*_id`, `errors`) are **dropped entirely**, as are unknown future keys.
- Each allowed value is stringified and HTML-escaped with `html.escape(str(value), quote=True)` before canonical JSON serialisation.
- Stable `f"{error.code}: {error.message}"` prefix, severity, R4 issue code and the `resourceType`/`issue`/`severity`/`code`/`diagnostics` shape are unchanged.
- Module + function docstrings now state that `diagnostics` is **untrusted text** that HTTP/HTML consumers MUST render escaped, and that it never carries a traceback or real-world identifier.

## 3. Regression tests added (strict, no skips)

In `test_fhir_operation_outcome.py`:
- raw `<script>` / `<b>` do not appear verbatim; escaped forms (`&lt;script&gt;`) appear for allowed keys; disallowed key and value are absent;
- machine code and message prefix preserved;
- exactly one issue with a valid R4 issue code and correct severity;
- `quote=True` escaping of `"`, `'`, `&`, `<`, `>` plus non-string values;
- closed-allowlist test covering all six keys;
- the one pre-existing exact-string test was updated **strictly** to the new sanitised expectation (not weakened).

## 4. Files changed (this cycle)

`backend/app/health_core/fhir/errors.py`, `backend/tests/health_core/test_fhir_operation_outcome.py`.

## 5. Verification

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_fhir_operation_outcome.py -q --tb=short
# 25 passed, 1 warning in 0.34s
```
Focused area files (authoritative JUnit): outcome 25, roundtrip 32, validation 40 = **97**. Ruff: `All checks passed!`.

## 6. Residual / blocked

- No HTTP/FHIR serving surface in the sandbox — a real adapter/endpoint is a separate owner-authorized program. This keeps WS-C at PARTIALLY VERIFIED; it is **not** a claim of FHIR production interoperability.
- Acceleration report §7 F-03 (documentation gap) was already closed earlier; I-2 closes the remaining diagnostic-sanitisation informational item.

**End of final report 03.**
