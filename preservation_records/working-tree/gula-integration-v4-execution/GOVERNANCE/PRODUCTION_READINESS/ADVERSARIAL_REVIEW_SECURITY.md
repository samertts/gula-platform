# Adversarial Security Review — Health Core Synthetic Slice

**Program:** GULA Production Readiness Acceleration Program
**Reviewer role:** Independent adversarial security reviewer (no implementation ownership)
**Repository:** `/home/samertts/workspace/projects/gula-integration` (READ-ONLY except this report)
**Date:** 2026-11-18
**Verdict:** **NO CRITICAL OR HIGH DEFECTS FOUND.** The reviewed slice is a synthetic, in-memory, non-routed isolation layer. Three LOW design limitations and two INFORMATIONAL hardening notes are recorded. No finding is exploitable through the current production surface because `health_core` has zero route/factory wiring and zero importers outside its own package and tests.

---

## 1. Mandate, scope, and authorization

### 1.1 What I was asked to do
Inspect actual on-disk code — not agent self-reports — in the scoped `health_core` packages, run nine categories of adversarial tests, and report evidence-based findings with severity, exact `file:line`, exploit/impact, concrete reproduction, and recommended fix. Explicitly identify zero-finding areas and separate "isolated synthetic design limitations" from "real exploitable defects."

### 1.2 Scope inspected
| Area | Files |
|---|---|
| Authorization | `backend/app/health_core/authorization/{models,engine,audit,guard,errors}.py` |
| Authorization tests | `backend/tests/health_core/test_authorization*.py` (+ `conftest.py`) |
| FHIR boundary | `backend/app/health_core/fhir/{support,deserializers,adapter,errors}.py` |
| Client integration | `backend/app/health_core/client_integration/{manifests,validators,observations,platforms,report}.py`; `backend/app/health_core/integration/auth_boundaries.py` |
| Terminology | `backend/app/health_core/terminology/{validators,models,registry,curated,releases,errors,ports}.py` |
| Shared support | `backend/app/health_core/common/{errors,ids}.py`; `backend/app/health_core/contracts/authorization.py`; `backend/app/health_core/identity/{synthetic,port}.py`; `backend/app/health_core/clinical/services.py` |

### 1.3 Write authorization (honored)
- **Sole authorized output:** `GOVERNANCE/PRODUCTION_READINESS/ADVERSARIAL_REVIEW_SECURITY.md` (this file).
- **Scratch only:** `/tmp/opencode/prodready/review_security/*.py`.
- **Not performed:** no source/test edits, no commit/stage/push/reset/clean, no DDL, no DB access, no route changes, no secret access, no fixes. All repository operations were reads or test executions against synthetic in-memory fixtures using `SYN-` identifiers only.

### 1.4 Toolchain
Pinned interpreter: `/tmp/opencode/mpi-venv/bin/python` (Python 3.12.13).
Canonical test invocation:
```
cd /home/samertts/workspace/projects/gula-integration/backend && \
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/tmp/opencode/mpi-venv/bin/python -m pytest <scratch test file> -q --tb=short -s
```

---

## 2. Executive summary

### 2.1 Severity counts
| Severity | Count | Finding IDs |
|---|---:|---|
| CRITICAL | **0** | — |
| HIGH | **0** | — |
| MEDIUM | **0** | — |
| LOW | **3** | L-1, L-2, L-3 |
| INFORMATIONAL | **2** | I-1, I-2 |

### 2.2 Test evidence totals
| Suite | Result |
|---|---|
| Existing `backend/tests/health_core/` (full slice) | **750 passed**, 1 deprecation warning, 7.18 s |
| Existing authorization subset (`test_authorization*.py`) | **62 passed**, 1 StarletteDeprecationWarning |
| Scratch adversarial suite (5 files, 9 mandated categories) | **60 passed**, 0 failed |
| — `test_adv_auth_engine.py` | 17 passed |
| — `test_adv_guard.py` | 9 passed |
| — `test_adv_audit.py` | 11 passed |
| — `test_adv_fhir.py` | 8 passed |
| — `test_adv_client_term.py` | 15 passed |

### 2.3 Key conclusion
All nine mandated adversarial categories were executed. Six produced **zero findings** outright; three produced only low/informational design observations in an isolated synthetic layer. The two most important claims — "no privilege escalation by forged roles/permissions/grants" and "no silent acceptance of unknown terminology codes" — were **confirmed by execution**, not by reading docstrings. The most significant assurance gap is an **overclaim in the audit-log docstring** (L-3): the chain detects interior tampering but cannot detect tail truncation or a fully recomputed forgery because it is unsigned, in-memory, and uses a public hash function.

---

## 3. Findings

### L-1 — LOW — Authorizing facade exposes unwrapped services publicly (design bypass)

**Location:** `backend/app/health_core/authorization/guard.py:86-88` (public `self.clinical`, `self.lab`, `self.engine`), with the guard contract stated at `guard.py:3-8`.

**What I did:** constructed `AuthorizedHealthCore`, then called `guard.clinical.organizations.register_organization(...)` and `guard.lab.place_order(...)` **directly**, bypassing every `guard.*` method. Also constructed the wrapped services standalone with no `AuthorizationEngine` at all.

**Exploit / impact:** An in-process caller holding a reference to the facade can perform writes that (a) skip policy evaluation entirely, (b) produce **zero audit records**, and (c) never populate the authoritative `ResourceAttributeIndex`. Confirmed: direct writes succeed, audit count remains 0, and `guard.attributes.snapshot()` has no entry for the created resource. Any future HTTP handler that accepts a facade object and calls `.clinical` / `.lab` instead of a guarded method would silently disable authorization and auditing.

**Why it is LOW, not HIGH:** `grep` confirms **no route wiring and no importers** of `health_core` outside its own package and tests (`app/factory.py` and `app/main.py` contain no `health_core` reference; `grep -rl health_core app --include=*.py | grep -v /health_core/ | grep -v test` returns nothing). There is currently **no reachable production attack path**. The module header explicitly documents the "callers must use `AuthorizedHealthCore`" contract. This is an isolated synthetic design limitation, not a live exploitable defect.

**Concrete reproduction:** `test_adv_guard.py::test_direct_wrapped_service_bypass_succeeds_without_audit` and `test_adv_guard.py::test_wrapped_service_constructible_without_engine`.

**Recommended fix:** Make `self.clinical` and `self.lab` private (`_clinical`, `_lab`) and expose them only via package-internal factory functions; add a test asserting no public attribute on the facade leads to an unguarded mutator. Alternatively, wrap services in a narrow interface that requires a `Principal` on every call.

**Disposition:** Source file is **in-scope** for review; remediation is **governance-blocked for me** by the review-only mandate (no fixes authorized) and should be scheduled as a hardening change in the authorization slice, not treated as a production incident.

---

### L-2 — LOW — Engine tenant equality trusts caller-supplied `tenant_id` on indexed reads

**Location:** `backend/app/health_core/authorization/engine.py:360` (`principal.tenant_id != resource.tenant_id`), `backend/app/health_core/authorization/guard.py:111-120` (`use_index=True` populates `ResourceContext.tenant_id` from the caller argument, while organization/facility/patient attributes come from the authoritative index), and the compensating service-layer check at `backend/app/health_core/clinical/services.py:106-111` (`_check_tenant` → `TenantMismatchError`).

**What I did:** created a resource under tenant A, then had a principal from tenant A request it while explicitly passing tenant A as `tenant_id` even though the resource belongs to tenant B (the attacker supplies its own tenant id, so `principal.tenant_id == resource.tenant_id`).

**Exploit / impact:** The policy engine returns `ALLOW ALLOW:EXPLICIT_PERMISSION`. It cannot detect the cross-tenant condition because the tenant context is caller-supplied and the index deliberately does not override it (`guard.py:113-120`). **No data is actually disclosed:** the underlying service then calls `_check_tenant(actual=<B>, expected=<A>)` and raises `TenantMismatchError` (`clinical/services.py:106-111`). Confirmed by `test_adv_guard.py::test_cross_tenant_read_with_own_tenant_id_is_blocked_at_service_layer`.

**Why it is LOW, not HIGH:** the enforced service-layer check is defense-in-depth that currently holds; there is no route wiring; the engine's own `DENY_TENANT` rule (`engine.py:358-361`) still stops the naive case where the caller passes the victim tenant id. The residual risk is a future new guarded method that forgets to call a tenant-checked service.

**Concrete reproduction output (verbatim):**
```
CROSS_TENANT_ENGINE_DECISION= ALLOW ALLOW:EXPLICIT_PERMISSION
```
...followed by `TenantMismatchError` at the service boundary — i.e. **engine allows, service denies**.

**Recommended fix:** in `ResourceAttributeIndex.put`, also bind and later enforce `tenant_id` from the stored `ResourceContext` when `use_index=True`; have `_authorize` reject any caller-supplied `tenant_id` that disagrees with the indexed tenant before invoking `engine.evaluate`. This converts a defense-in-depth dependency into a single authoritative check.

**Disposition:** **in-scope** engine/guard design hardening; **governance-blocked for me** by review-only mandate.

---

### L-3 — LOW — Audit docstring overclaims tamper detection; tail truncation and full rehash forgery undetected

**Location:** `backend/app/health_core/authorization/audit.py:5-6` (docstring: "detects edited, removed, reordered or re-hashed records"), `audit.py:41-43` (public `compute_record_hash`), `audit.py:94-111` (`verify_audit_chain`, forward-only), `audit.py:114-176` (in-memory `AuthorizationAuditLog`).

**What I did:** on a 5-record pristine chain I (a) mutated a field, (b) reordered records, (c) deleted a middle record, (d) deleted the first record, (e) deleted the last record, and (f) rebuilt the entire chain with consistent recomputed hashes using the public `compute_record_hash`. I also verified denial-path auditing separately.

**Results (verbatim):**
```
PRISTINE= True 5
TAMPER_FIELD_ERRORS= ('SYN-AUD-1606070E9A30: record hash does not match its payload',)
REORDER_ERRORS= ('SYN-AUD-8552A2E3690D: expected sequence 2, got 4', 'SYN-AUD-8552A2E3690D: predecessor hash does not match the chain', 'SYN-AUD-CC02E86DAD7D: predecessor hash does not match the chain')
DELETE_ERRORS= ('SYN-AUD-7F0A66F3A195: expected sequence 3, got 4', 'SYN-AUD-7F0A66F3A195: predecessor hash does not match the chain', 'SYN-AUD-23B386C62F6D: expected sequence 4, got 5')
DELETE_FIRST_ERRORS= ('SYN-AUD-64E7BBB04949: expected sequence 1, got 2', 'SYN-AUD-64E7BBB04949: predecessor hash does not match the chain', 'SYN-AUD-BA0AA1363805: expected sequence 2, got 3', 'SYN-AUD-788E210DA128: expected sequence 3, got 4')
DELETE_LAST_ERRORS= () valid= True
REHASH_FORGERY_VALID= True errors= ()
```

**Exploit / impact:** An attacker able to mutate the in-memory record list can remove the tail (erase the most recent decision, including a denial) or rewrite the whole history coherently and pass `verify()`. The chain has no signature, no external anchor (e.g. append-only file / WORM store / notary), and lives in process memory; `compute_record_hash` is public. Because there is no route or persistence, **no production compromise results today**. The real defect is the **documentation overclaim**: operators reading `audit.py:5-6` may rely on tamper-detection guarantees the implementation does not provide.

**Confirmed non-issues in the same category:** records are frozen dataclasses; `records()` returns an immutable tuple snapshot; there is no public mutation/delete/truncate method on `AuthorizationAuditLog`; every denial appends exactly one record with the correct policy id; the denial path does **not** bypass auditing. Verified policies observed:
```
DENIAL_POLICIES= ['ALLOW:EXPLICIT_PERMISSION', 'DENY:MISSING_PERMISSION', 'DENY:CROSS_TENANT']
```

**Concrete reproduction:** `test_adv_audit.py::test_delete_last_record_is_not_detected`, `test_adv_audit.py::test_full_rehash_forgery_is_not_detected`, `test_adv_audit.py::test_denials_are_audited_with_correct_policy_ids`.

**Recommended fix:** (1) correct the docstring to state the chain detects interior edits/reorders/deletions but **not** tail truncation or coherent rewrites without an external anchor; (2) for production-grade assurance, sign each record with a key held outside the process and anchor the head hash to durable append-only storage; (3) add a test asserting the documented limitation so the overclaim cannot silently return.

**Disposition:** documentation correction is **in-scope**; cryptographic signing / external anchoring is **governance-blocked** — it requires an architectural decision on key custody, persistence, and timestamp authority, and is explicitly outside this synthetic slice. Review-only mandate prohibits me from making even the docstring edit.

---

### I-1 — INFORMATIONAL — `is_synthetic_id` is a weak prefix/length predicate despite its docstring

**Location:** `backend/app/health_core/common/ids.py:29-31`.

**Docstring claims:** "True only for strings produced by `new_synthetic_id`" (`ids.py:30`). **Actual predicate:** `isinstance(str) and startswith("SYN-") and len > 8`.

**Observed (verbatim):**
```
WEAK_SYN_ACCEPTED= ['SYN-12345', 'SYN-ABCDE', 'SYN-!!!!!!!!!', 'SYN-99999999999999999999']
```

**Exploit / impact:** none demonstrated. All strict consumers I tested use `reject_national_identifier` (`ids.py:34-52`) and the FHIR validators (`fhir/support.py:294,311,351`) instead of relying solely on `is_synthetic_id`, so no real NID or malformed reference passed. Risk is future misuse: a caller trusting the docstring could accept an attacker-controlled `SYN-!!!!!!!!!` as a legitimate generated id.

**Recommended fix:** tighten to `^SYN-[A-Z]{2,8}-[0-9A-F]{12}$` matching `new_synthetic_id`'s output (`ids.py:21-26`), or rename to `looks_like_synthetic_id` and update the docstring.

**Disposition:** **in-scope** one-line hardening; **governance-blocked for me** by review-only mandate.

---

### I-2 — INFORMATIONAL — OperationOutcome `diagnostics` echoes error `details` verbatim

**Location:** `backend/app/health_core/fhir/errors.py:146-149` and `157`.

**Observed (verbatim):**
```
OO_DIAGNOSTICS= INVALID_FHIR_RESOURCE: bad <script>alert(1)</script> | {"field":"subject"}
OO_WITH_DETAILS= INVALID_SYNTHETIC_REFERENCE: bad | {"field":"patient_ref","raw":"SYN-PAT-0001"}
```

**Exploit / impact:** `diagnostics` is a string in a JSON `OperationOutcome` body. A `<script>` payload in client-supplied input is echoed, but as JSON text — **not executable in the API response itself**. Risk is contextual: an HTML-based consumer that renders `diagnostics` unescaped would create a reflected-XSS sink. All values I observed were synthetic fixtures (`SYN-PAT-0001`) or attacker-supplied test strings; **no real patient data, secret, or national identifier appeared in any error body**. A precise repository-wide grep found **zero** `print(...)` / `logging.*` / `logger.*` / `log.*(...)` calls anywhere in `backend/app/health_core/`.

**Recommended fix:** allowlist the keys permitted in `details` and HTML-escape string values before embedding them in `diagnostics`; document that consumers must treat `diagnostics` as untrusted text.

**Disposition:** **in-scope** adapter hardening; **governance-blocked for me** by review-only mandate.

---

## 4. Zero-finding areas (explicit)

Each of the nine mandated test categories was executed. Results:

| # | Category | Result | Evidence |
|---|---|---|---|
| 1 | Facade bypass via direct service | **Finding L-1 (LOW)** — confirmed bypass exists in-process; **not reachable from any route** | `test_adv_guard.py` (9 passed); route-wiring greps empty |
| 2 | Forge/grant escalation — injected roles/permissions, forged grants, malformed tenant ids, None/empty attrs | **ZERO FINDINGS** — 17/17 passed | `test_adv_auth_engine.py`; forged roles/permissions/grants rejected, malformed ids rejected, `None` action → `DENY_NO_POLICY`, unauthenticated → `DENY_UNAUTHENTICATED`, expired/foreign grants rejected |
| 3 | Cross-tenant non-disclosure | **ZERO DATA DISCLOSURE** — service layer always blocks (engine-level nuance = L-2) | `test_adv_auth_engine.py`, `test_adv_guard.py`; `TenantMismatchError` raised; index refuses tenant reassignment |
| 4 | Revocation ordering (grant→revoke and revoke→grant) | **ZERO FINDINGS** — both orders deny immediately; role-permission revocation correctly scoped | `test_adv_auth_engine.py::test_revocation_*` |
| 5 | Audit chain tampering + denial-path audit bypass | **Partial** — interior tamper/reorder/delete all detected; **L-3** for tail truncation/full rehash; **denial-path audit bypass: ZERO FINDINGS** (exactly one record per denial) | `test_adv_audit.py` (11 passed) |
| 6 | Synthetic-id validation — real NIDs, digit-only, malformed refs, cross-resource mismatches | **ZERO REJECTION BYPASS** — all invalid forms rejected; weak predicate = I-1 only | `test_adv_fhir.py` (8 passed); real-looking NIDs, digit-only, malformed refs, absolute URLs, extra keys, cross-resource type mismatches, wrong-system identifiers all rejected |
| 7 | Data-leak grep — logging/printing/error echo | **ZERO logging/printing**; error echo limited to synthetic values = I-1/I-2 notes | precise grep exit 1 (no matches); `test_adv_fhir.py` outputs above |
| 8 | Anonymous/bypass auth in client validators | **ZERO FINDINGS** — all tampered manifests flagged fail-closed | `test_adv_client_term.py` (15 passed); flags `ANONYMOUS_WRITES_ALLOWED`, `IMPLICIT_PERMISSION_MODEL`, `NON_EXACT_ROLE_MATCH`, `AUTH_BYPASS_PATH`, `AUTH_ANONYMOUS_READ`, `PUBLIC_WRITE`, `ANONYMOUS_ROLE`; `is_permitted(ANONYMOUS)` always False |
| 9 | Unknown terminology code silently accepted | **ZERO FINDINGS** — unknown well-formed codes → `UNVERIFIED`/`accepted=False`; only curated codes → `VALID`/`accepted=True`; malformed/SYN-/real-id-shaped → `INVALID`; unknown system raises | `test_adv_client_term.py`; `ICD_UNKNOWN= UNVERIFIED accepted= False`, `LOINC_UNKNOWN= UNVERIFIED accepted= False`, `UCUM_UNKNOWN= UNVERIFIED accepted= False`, `ICD_KNOWN= J18.9 VALID accepted= True`, `UNKNOWN_SYSTEM_RAISES= UnknownTerminologySystemError` |

**Additional zero-finding observations:**
- No policy rule-ordering defect: `DENY_NO_POLICY` → `DENY_UNAUTHENTICATED` → `DENY_TENANT` → revocation → permission → scopes, exactly as implemented at `engine.py:352-390`.
- No forged grant acceptance, no cross-tenant resource indexing, no `None`/empty-attribute crash — all denied cleanly with public, non-revealing reasons.
- No `FULL_RELEASE_CONFORMANCE` or `FULL_RELEASE` claim emitted by the terminology adapters; all results carry `PARTIALLY_VERIFIED` provenance.

---

## 5. Exact commands and outputs

### 5.1 Existing baseline
```
$ cd /home/samertts/workspace/projects/gula-integration/backend
$ ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
    /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/ -q --tb=short
...
750 passed, 1 warning in 7.18s
```
The single warning is `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` (unrelated to this slice's behavior).

### 5.2 Adversarial batch 1 — engine, guard, audit, FHIR (45 tests)
```
$ cd /home/samertts/workspace/projects/gula-integration/backend
$ ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
    /tmp/opencode/mpi-venv/bin/python -m pytest \
    /tmp/opencode/prodready/review_security/test_adv_auth_engine.py \
    /tmp/opencode/prodready/review_security/test_adv_guard.py \
    /tmp/opencode/prodready/review_security/test_adv_audit.py \
    /tmp/opencode/prodready/review_security/test_adv_fhir.py \
    -q --tb=short -s
```
Output (verbatim):
```
................WEAK_SYN_ACCEPTED= ['SYN-12345', 'SYN-ABCDE', 'SYN-!!!!!!!!!', 'SYN-99999999999999999999']
.....CROSS_TENANT_ENGINE_DECISION= ALLOW ALLOW:EXPLICIT_PERMISSION
.....PRISTINE= True 5
.TAMPER_FIELD_ERRORS= ('SYN-AUD-1606070E9A30: record hash does not match its payload',)
.REORDER_ERRORS= ('SYN-AUD-8552A2E3690D: expected sequence 2, got 4', 'SYN-AUD-8552A2E3690D: predecessor hash does not match the chain', 'SYN-AUD-CC02E86DAD7D: predecessor hash does not match the chain')
.DELETE_ERRORS= ('SYN-AUD-7F0A66F3A195: expected sequence 3, got 4', 'SYN-AUD-7F0A66F3A195: predecessor hash does not match the chain', 'SYN-AUD-23B386C62F6D: expected sequence 4, got 5')
.DELETE_FIRST_ERRORS= ('SYN-AUD-64E7BBB04949: expected sequence 1, got 2', 'SYN-AUD-64E7BBB04949: predecessor hash does not match the chain', 'SYN-AUD-BA0AA1363805: expected sequence 2, got 3', 'SYN-AUD-788E210DA128: expected sequence 3, got 4')
.DELETE_LAST_ERRORS= () valid= True
.REHASH_FORGERY_VALID= True errors= ()
...DENIAL_POLICIES= ['ALLOW:EXPLICIT_PERMISSION', 'DENY:MISSING_PERMISSION', 'DENY:CROSS_TENANT']
........OO_DIAGNOSTICS= INVALID_FHIR_RESOURCE: bad <script>alert(1)</script> | {"field":"subject"}
.OO_WITH_DETAILS= INVALID_SYNTHETIC_REFERENCE: bad | {"field":"patient_ref","raw":"SYN-PAT-0001"}
.
45 passed in 0.60s
```

### 5.3 Adversarial batch 2 — client manifests and terminology (15 tests)
```
$ ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
    /tmp/opencode/mpi-venv/bin/python -m pytest \
    /tmp/opencode/prodready/review_security/test_adv_client_term.py -q --tb=short -s
```
Output (verbatim):
```
CLIENT_VALID_ERRORS= ()
.ANON_WRITE_ERRORS= ('ANONYMOUS_WRITES_ALLOWED',)
.IMPLICIT_PERMISSION_ERRORS= ('IMPLICIT_PERMISSION_MODEL',)
.NON_EXACT_ROLE_ERRORS= ('NON_EXACT_ROLE_MATCH',)
.BYPASS_PATH_ERRORS= ["AUTH_BYPASS_PATH: read:practitioner: ('/debug/noauth',)"]
.ANON_READ_ERRORS= ['AUTH_ANONYMOUS_READ: read:practitioner']
.PUBLIC_WRITE_ERRORS= ['PUBLIC_WRITE: write:practitioner']
.ANON_ROLE_ERRORS= ['ANONYMOUS_ROLE: read:practitioner']
..ICD_UNKNOWN= UNVERIFIED accepted= False
.LOINC_UNKNOWN= UNVERIFIED accepted= False
.UCUM_UNKNOWN= UNVERIFIED accepted= False
.ICD_KNOWN= J18.9 VALID accepted= True
.MALFORMED_CODES_ALL_INVALID= True
.UNKNOWN_SYSTEM_RAISES= UnknownTerminologySystemError
.
15 passed in 0.58s
```

### 5.4 Reachability greps (both empty → exit 1)
```
$ grep -rn "health_core" app/factory.py app/main.py
(no output) ROUTE_WIRING_GREP_EXIT=1

$ grep -rl "health_core" app --include="*.py" | grep -v "/health_core/" | grep -v test
(no output) EXTERNAL_IMPORTERS_EXIT=1
```

### 5.5 Data-leak greps
```
$ grep -rnE "print\(|logging\.|logger\.|log\.(debug|info|warning|error|critical|exception)" \
    app/health_core --include="*.py"
# 10 hits — all false positives: the substring "print(" inside "_fingerprint(" in
# clinical/services.py (idempotency fingerprinting), not any print/log call.

$ grep -rnE "(^|[^_a-zA-Z])(print|logging\.[a-z]+|logger\.[a-z]+|log\.(debug|info|warning|error|critical|exception))\(" \
    app/health_core --include="*.py"
(no output) PRECISE_DATA_LEAK_GREP_EXIT=1
```

### 5.6 Note on scratch-test iterations
Two early scratch assertions failed due to **my incorrect assumptions**, not implementation defects: (a) I assumed `ENCOUNTER_READ` required `CLINICIAN` when its configured minimum role is `VIEWER`; (b) my cross-tenant fixture lacked the foreign-facility scope it needed to reach the intended policy branch. I corrected the fixtures and re-ran; all 60 final tests pass. One terminology assertion failed because `I10` **is** curated; I replaced it with `Z99.9`, which is well-formed but not curated, and re-ran. These corrections are disclosed for transparency.

---

## 6. Review limitations

1. **Synthetic, non-production slice.** All fixtures use `SYN-` identifiers, in-memory repositories, and no PostgreSQL/Redis. Findings describe this slice only; they are not statements about the wider GULA platform.
2. **No route/factory wiring.** Verified by grep (`§5.4`). Consequently every "bypass" finding is an in-process design limitation, **not** an externally reachable exploit. If this slice is wired into production later, L-1 and L-2 must be re-evaluated at HIGH/MEDIUM.
3. **Audit chain is unsigned and in-memory by design.** No external anchor exists, so L-3's tail-truncation/rehash behavior is inherent to the design; a true tamper-evidence guarantee needs key custody and durable storage decisions outside my mandate.
4. **Review-only mandate.** No fix, commit, test addition to the repository, config change, or document other than this report was made. All adversarial tests live under `/tmp/opencode/prodready/review_security/`.
5. **No coverage of runtime transport.** TLS, reverse-proxy headers, CORS, CSRF, session/token issuance, rate limiting, and HTTP-level error handling are out of scope; this module issues no tokens and reads no sessions (`auth_boundaries.py:1-9`).
6. **Terminology verification is intentionally partial.** Adapters validate structure + a small curated allowlist. `UNVERIFIED` is the honest outcome for most real codes; absence of full official-release conformance is documented by the implementation, not a security finding.
7. **XSS note (I-2) is contextual.** The `OperationOutcome` is JSON; exploitability depends entirely on an HTML consumer rendering `diagnostics` unescaped. I did not audit any consumer (none exists in this slice).
8. **No negative result claimed beyond tested inputs.** "Zero findings" means zero findings for the specific adversarial inputs executed and the files read, not a formal proof of absence.

---

## 7. Final verdict

The scoped `health_core` slice demonstrates **deny-by-default authorization, no forge/escalation path, correct revocation ordering, fail-closed client/terminology validators, and strict synthetic-reference validation** under adversarial execution. The three LOW findings are design-hardening items in an unreferenced synthetic layer; the two INFORMATIONAL notes are documentation/output-hygiene improvements. **Nothing in this review blocks production readiness on security grounds, provided the slice remains unwired.** Before any future wiring into a live request path, L-1 and L-2 must be remediated and re-reviewed, and the audit-log claim in L-3 must either be corrected or backed by a signed, externally anchored log.

**Report status:** COMPLETE — independent adversarial review, evidence-based, no repository modifications beyond this file.
