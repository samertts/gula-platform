# Team A — API and Interoperability Reassessment (A4)

**Audit ID:** A4
**Date:** 2026-11-18
**Repository:** `gula-integration`
**Audited ref:** working tree at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling boundary:** `/home/samertts/workspace/projects/gula-platform` observed read-only at `f478676b`; never modified.
**Mode:** adversarial, READ-ONLY, static/synthetic evidence only.
**Machine-readable companion:** `GOVERNANCE/ADVERSARIAL_ASSURANCE/FINDINGS_A4_DATA_API.json`

---

## 1. Decision boundary (unchanged)

No protected verdict was altered, closed, or downgraded by this audit.

| Decision / finding | Owner state after this audit |
|---|---|
| Release decision (`GOVERNANCE/FINAL_DECISION.md`) | **HOLD** — unchanged; protected MD5 `effdfeaf10234678d83b2668c4489552` verified matching on disk |
| MPI verdict | **REJECT** — unchanged (A3 boundary respected) |
| MP-001; ODR-001…ODR-004; D-020; D-021; ADR-A…ADR-J | **UNCHANGED** — no approval inferred |
| AUD-02 / AUD-07 / AUD-16 | **OPEN** — unchanged |
| T6 FHIR router | **NON-ACTIVATED** — confirmed; WS-E guard confirmed holding |
| ADR-A / 284-table gap | **BLOCKED** — unchanged |

Assurance vocabulary is limited to `IMPLEMENTED`, `TESTED`, `INTEGRATED`, `BLOCKED`, `NOT IMPLEMENTED`. All nine findings below have `status = DISCOVERED` in the JSON artifact. **No audited work is awarded `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`** — that is Team C authority only.

---

## 2. Method and evidence limits

**Performed:** AST enumeration of route functions, router mounting analysis in `factory.py`/`main.py`, call-site and dependency graph grep for auth/token flows, static reads of FHIR/HL7/DICOM/terminology/OAuth/OIDC implementations, rate-limit wiring, error shapes, and protected governance evidence. Synthetic reproduction/falsification designs were produced for every finding.

**Not performed (mandate prohibitions):** no server start, no HTTP request or network access, no DB connection, no git stage/commit/push, no real patient data, no secrets, no modification of pre-existing files.

**Coverage note:** 2408 route functions enumerated, 83 active factory routers. Full line-by-line semantic review of all 2408 endpoints was not possible; risk-sampling was used, and every initially flagged auth candidate was individually falsified by reading router-level dependencies and helper code before deciding not to raise a finding.

---

## 3. Corroborated non-findings (recorded to prevent false positives)

| Candidate | Static check | Disposition |
|---|---|---|
| "Missing router authentication" | NIAM account endpoints return 410; ecosystem and blood-bank routers carry router-level `system:admin`; contracts use `_READ`/`_WRITE`; certification uses `_READ` | **Falsified** — no unauthenticated sensitive endpoint confirmed |
| "Missing rate limiting" | `GlobalRateLimitMiddleware` present and wired at `backend/app/factory.py:429,443`; all paths except `_ALWAYS_ALLOWED_PATHS` covered by a coarse IP budget | **Falsified** — no finding raised |
| "T6 FHIR router is live / spoofable header principal" | No `fhir_http` import/reference in `factory.py` or `main.py`; only `capabilities.fhir_interoperability` is mounted at `backend/app/factory.py:656-658`; WS-E guard at `backend/tests/health_core/test_quality_review_static.py:30,407,410-418` holds; `FINAL_DECISION.md` MD5 matches | **Falsified as active defect**; residual activation risk recorded as AUD-API-009 |
| "JWKS/discovery failures are fail-open" | Discovery/JWKS posture fail-closed (JWKS returns 503; HS256-only) | **Corroborated** — no finding raised on that aspect |
| "Migration chain has 6 heads" | Refined AST scan: single root, single head, no cycles/duplicates | **Falsified** — see database report §3 |

Active implementation facts are `IMPLEMENTED` observations only; none are release certifications.

---

## 4. New API / interoperability findings (all `status = DISCOVERED`)

Full machine-readable detail is in `FINDINGS_A4_DATA_API.json`.

### AUD-API-001 — Active admin endpoint `GET /integration/standards` deterministically raises `AttributeError` (HTTP 500)

- **Severity:** HIGH; **likelihood:** HIGH; **classification:** breaking; **owner_gated:** false.
- **Evidence:** `backend/app/integration/routes.py:171-205` reads `fhir.fhir_version`, `fhir.capabilities`, `hl7.hl7_version`, `hl7.supported_message_types`, `dicom.supported_sop_classes`, `ihe.supported_profiles`, `terms.terminology_systems`; the defining classes expose different names — `backend/app/integration/standards/fhir.py:20-48` (`_version`/`version()`), `hl7.py:44-60` (`_version`/`parse`/`create_message`), `dicom.py:37-61` (`dicom_services()`/`modalities()`), `ihe.py:20-60` (`list_profiles()`/`_supported_profiles`), `terminology.py:25-69` (`list_systems()`/`_supported_systems`); `backend/app/factory.py:766-767` mounts this router in production startup.
- **Reproduction:** for each of the six attribute names, grep the defining class module — no definition exists; any `GET /integration/standards` hits `AttributeError` before returning. **Falsification:** add `@property` definitions for all six names and re-check — no such properties exist. Static deduction only; no server was started.
- **Root cause:** conformance-display endpoint written against an assumed service API the standards classes never implemented; no endpoint test covers it.
- **Impact:** a mounted, `system:admin`-protected observability endpoint always fails (500) and masks whether FHIR/HL7/DICOM/terminology claims are real.
- **Remediation:** rewrite the endpoint to call real accessors (`fhir.version()`, `ihe.list_profiles()`, `terms.list_systems()`, `dicom.dicom_services()`, etc.) and add a focused endpoint test; do not invent attributes to satisfy it.
- **Alternatives:** (1) real accessors + test (recommended); (2) remove endpoint from schema until implemented; (3) thin `@property` aliases (removes 500 but preserves conformance-theater semantics — not recommended).

### AUD-API-002 — Every OAuth2-issued access token is rejected by the platform's own protected endpoints

- **Severity:** HIGH; **likelihood:** HIGH; **classification:** breaking; **owner_gated:** true.
- **Evidence:** `backend/app/security/oauth2_provider.py:119-128` sets payload `type='oauth2_access'`; `backend/app/security/auth.py:99-106` `decode_token()` returns `None` unless `type == 'access'`; `backend/app/security/dependencies.py:37-50,71-75` uses `decode_token()` and requires `user_id`; `backend/app/security/oauth2_provider.py:151-158` `decode_oauth2_token()` is the only decoder accepting `oauth2_access` and has **zero call sites** anywhere in `backend/app`; `backend/app/routes/oauth2.py:144-160` issues these tokens.
- **Reproduction:** static data-flow: `/oauth2/token` → `create_access_token_oauth2(type='oauth2_access')` → Bearer to any protected route → `get_current_user()` → `decode_token()` → type mismatch → `None` → 401. **Falsification:** show a route/dependency calling `decode_oauth2_token()`, or a token issue path using `type='access'` with `user_id` — neither exists.
- **Root cause:** OAuth2 provider built as a parallel token kind with its own orphaned decoder instead of integrating with the canonical `decode_token`/`get_current_user` chain.
- **Impact:** the entire OAuth2/OIDC authorization-code and refresh-token flow is non-functional against GULA's own API — tokens can be minted but never used; public discovery advertises them as usable. Any relying party fails at first call.
- **Remediation:** owner decision on OAuth2's role; then either unify token type to `access` with `user_id`/`lab_id`/`perm_ver` claims, or wire `decode_oauth2_token` into an accepted dependency with defined authorization semantics. Add an end-to-end mint-then-call test.
- **Alternatives:** (1) unify into canonical token pipeline (recommended); (2) separate decoder + explicit OAuth2 dependency on selected routers; (3) mark OAuth2 NOT INTEGRATED and remove from discovery until owner rules.

### AUD-API-003 — OAuth client registration and scope/grant assignment are ungoverned; `grant_types` never enforced

- **Severity:** MEDIUM; **likelihood:** MEDIUM; **classification:** owner-decision; **owner_gated:** true.
- **Evidence:** `backend/app/routes/oauth2.py:54-80` `POST /oauth2/register` requires only `get_current_user` (no admin permission) while caller chooses `allowed_scopes`, `grant_types`, `response_types`, `token_endpoint_auth_method`; `:83-141` `/authorize` stores caller-supplied `scope` verbatim at line 127 without checking `client.allowed_scopes`; `:144-160` `/token` dispatches on `data.grant_type` without checking `client.grant_types`; `:242-249` `token_endpoint_auth_method='none'` skips client secret verification; `backend/app/security/oauth2_provider.py:212-216` discovery advertises `'none'` and scopes `openid/profile/email/read/write`.
- **Reproduction:** any authenticated user can register a public client with `allowed_scopes=['system:admin']` and arbitrary grants, then request arbitrary scope at `/authorize`. **Falsification:** show a permission dependency on `/register` or a scope/grant allowlist at issuance — absent in cited lines. Present impact is bounded because `get_current_user` requires `user_id` (client-credentials tokens have none) and RBAC reads roles, not token scope.
- **Root cause:** client onboarding treated as a self-service utility; no governance boundary around OAuth2 trust anchors.
- **Impact:** attacker-controlled scope claims in minted tokens; public clients with arbitrary grants; least-privilege gap. Latent rather than confirmed under current RBAC.
- **Remediation:** require admin/governance permission for registration; validate requested scope against `allowed_scopes` at `/authorize`; enforce `grant_types`/`response_types` at `/token` and `/authorize`; restrict `'none'` to explicitly approved public clients.
- **Alternatives:** (1) govern registration + enforce all allowlists (recommended); (2) disable registration/issuance until owner rules (safe, matches current non-functional state); (3) permissive with monitoring (not recommended for a national platform).

### AUD-API-004 — JWT validation enforces only `exp`/`iat` — no audience, issuer or subject binding

- **Severity:** MEDIUM; **likelihood:** MEDIUM; **classification:** breaking; **owner_gated:** true.
- **Evidence:** `shared/auth/jwt.py:18-25` `_validate_claims()` registry contains `exp` and `iat` only; `:60-72` `decode_access_token()` calls `_validate_claims` with no `aud`/`iss` checks; `backend/app/security/oauth2_provider.py:119-129` access-token payload carries `jti/client_id/type/user_id/scope` but no `aud` or `iss`; `backend/app/security/auth.py:99-106` adds only a type check.
- **Reproduction:** read the `JWTClaimsRegistry` construction at `shared/auth/jwt.py:19-22` — keys are `exp`, `iat`. **Falsification:** show `aud`/`iss` in the registry or the OAuth2 payload — absent.
- **Root cause:** validation designed for a single shared-secret audience; no multi-client/national relying-party model.
- **Impact:** tokens minted for one client/realm are accepted anywhere the shared HMAC key is known; no audience isolation between national services; contributes to the OIDC claim-conformance gap.
- **Remediation:** add `aud`/`iss` to issued tokens and validate configured expected values in `decode_access_token`; coordinate with AUD-API-002 so one decoder enforces the full claim set.
- **Alternatives:** (1) full claims validation (recommended); (2) document single-audience limitation and keep HOLD (current posture); (3) per-audience signing keys (higher key-management cost; ODR-gated asymmetric decision pending).

### AUD-API-005 — OAuth2 introspection and revocation endpoints require no client authentication

- **Severity:** MEDIUM; **likelihood:** MEDIUM; **classification:** breaking; **owner_gated:** true.
- **Evidence:** `backend/app/routes/oauth2.py:163-188` `POST /oauth2/introspect` has no client-auth dependency and returns `active`, `client_id`, `user_id`, `scope`, `token_type`, `exp`; `:191-205` `POST /oauth2/revoke` has no client authentication — any caller can revoke a token; `backend/app/security/oauth2_provider.py:205-210` advertises both endpoints.
- **Reproduction:** both function signatures take only `data/request/db` — no `_authenticate_client()` call (contrast `/token` at line 150). **Falsification:** show a client-auth dependency or `_authenticate_client()` inside introspect/revoke — absent.
- **Root cause:** RFC 7662 / RFC 7009 client-authentication requirements were not implemented; endpoints are simple token-hash lookups.
- **Impact:** token information disclosure to any holder of a token string and unauthenticated DoS via revocation. The global IP rate limit is a coarse mitigation, not client authentication.
- **Remediation:** require client authentication on both endpoints and scope introspection response fields to the authenticated client's entitlement (RFC 7662 §2.2).
- **Alternatives:** (1) client auth + field scoping (recommended); (2) remove from discovery and disable until implemented; (3) rely on global rate limit (not recommended).

### AUD-API-006 — Active FHIR R4 router accepts arbitrary unvalidated JSON and returns non-FHIR errors

- **Severity:** MEDIUM; **likelihood:** HIGH; **classification:** breaking; **owner_gated:** true.
- **Evidence:** `backend/app/factory.py:656-658` mounts `capabilities.fhir_interoperability.routes` (unlike the non-activated T6 router); `backend/app/capabilities/fhir_interoperability/schemas.py:21-22` sets `ConfigDict(extra='allow')`; `service.py:56,67` persists `payload.model_dump(exclude_none=True)` verbatim into `FHIRResourceRecord.resource`; `routes.py:26-31,107-112,155-156` raises plain `HTTPException(detail=str)`, not `application/fhir+json` `OperationOutcome`; `schemas.py:79-86` CapabilityStatement declares `fhirVersion 4.0.1` with no type/profile/terminology validation.
- **Reproduction:** `POST /fhir-interoperability/resources` with a valid `resourceType` plus arbitrary extra fields — `schemas.py:22` allows them and `service.py:56` stores them; trigger 404 at `routes.py:155-156` and observe a plain `{"detail": ...}` body, not an R4 OperationOutcome. **Falsification:** point to a canonicalization/allowlist step or an OperationOutcome exception handler on this router — neither exists (the non-activated T6 router does implement OperationOutcome but is not mounted).
- **Root cause:** the mounted capability is a thin persistence facade; conformance is represented by type names and a CapabilityStatement rather than validation of FHIR structures, references, profiles, or terminology.
- **Impact:** stored PHI resources may contain arbitrary client-controlled fields; clients cannot rely on FHIR error semantics; nominal R4 conformance could be mistaken for real conformance.
- **Remediation:** set `extra='forbid'` (or canonicalize through the in-repo Health Core `FhirR4Adapter`), validate terminology/references, and add an exception handler emitting R4 OperationOutcome for all failures on this router.
- **Alternatives:** (1) reuse canonical adapters + OperationOutcome (recommended; reuse before build); (2) keep facade but document NOT FHIR-conformant and remove R4 claims; (3) activate T6 after a real auth boundary (owner-gated, D-020).

### AUD-API-007 — HL7 OBX numeric values `NaN`/`Infinity` cause HTTP 500 in active FHIR conversion endpoint

- **Severity:** LOW; **likelihood:** MEDIUM; **classification:** unresolved; **owner_gated:** false.
- **Evidence:** `backend/app/capabilities/fhir_interoperability/hl7.py:96-107` calls `float(value)` with no `isfinite()` guard and places the result in `valueQuantity.value`; `backend/app/capabilities/fhir_interoperability/routes.py:71-85` returns the bundle dict through FastAPI JSON serialization; Starlette `JSONResponse.render` (verified from installed source) uses `json.dumps(..., allow_nan=False)`.
- **Reproduction:** send an ORU^R01 message whose OBX-5 is `NaN` (or `Infinity`) → `_observation_value` returns `float('nan')` → Starlette raises `ValueError` under `allow_nan=False` → 500. **Falsification:** show a `math.isfinite()` guard or string coercion before serialization — absent.
- **Root cause:** numeric parsing accepts all `float()` lexical forms without domain validation; response serialization is strict RFC 8259.
- **Impact:** a router-level `system:admin` request can produce 500s and log noise; corrupt numeric FHIR observations if a non-strict serializer is later introduced.
- **Remediation:** reject non-finite floats (`math.isfinite`) and emit `valueString` or a 422 for non-numeric/non-finite OBX values; bound OBX-5 length.
- **Alternatives:** (1) `isfinite` guard (recommended); (2) coerce to string (loses numeric semantics); (3) Pydantic strict `Decimal` parsing.

### AUD-API-008 — Terminology/DICOM "support" is declaration-only — hardcoded lists with no validation engine

- **Severity:** MEDIUM; **likelihood:** HIGH; **classification:** unresolved; **owner_gated:** true.
- **Evidence:** `backend/app/integration/standards/terminology.py:31-42` supported systems from a hardcoded string map with zero concepts; `:50-54` `validate()` delegates to an empty `CodeSystem` for known systems (always False unless concepts are registered; fallback branch unreachable for supported systems); `:69` `is_supported()` returns True purely from the map; `backend/app/integration/standards/dicom.py:37-61` dataclasses and service/modality name lists, no DIMSE/network/UID validation; `backend/app/integration/standards/fhir.py:32-35` `validate()` checks only presence of `resourceType`; `backend/app/health_core/terminology/validators.py:225-303` real LOINC check-digit/ICD-10/UCUM validators exist here but WS-E keeps that package out of `factory.py`/`main.py` (`backend/tests/health_core/test_quality_review_static.py:120-130`).
- **Reproduction:** instantiate `TerminologyService`; `get_system('LOINC')` creates an empty CodeSystem (`:34-39`); `validate('LOINC','718-7')` evaluates `'718-7' in {}` → False while `is_supported('LOINC')` → True. No DICOM protocol module exists in `app/integration/standards/dicom.py`. **Falsification:** show a caller registering curated concepts into the active service or a real DICOM engine — grep shows none.
- **Root cause:** standards support modeled as capability descriptors for reporting, not validation engines; robust validators live in an intentionally non-wired synthetic slice.
- **Impact:** LOINC/SNOMED/ICD-10/UCUM and DICOM claims in `/integration/standards` and `NATIONAL_SERVICE_CONTRACTS` are not enforceable in the active runtime; downstream clinical data can carry unvalidated codes/units.
- **Remediation:** either wire curated Health Core validators into the active boundary through an adapter (respecting WS-E — do NOT move HTTP code into health_core) or explicitly reclassify standards support as `NOT IMPLEMENTED` in contracts; add code-system content before claiming validation.
- **Alternatives:** (1) reuse canonical validators via an outside adapter (recommended); (2) relabel descriptors "declared, not validated" and keep HOLD; (3) build new validators (violates reuse-before-build).

### AUD-API-009 — T6 FHIR router remains non-activated with a synthetic header principal — activation risk if wired unchanged

- **Severity:** MEDIUM; **likelihood:** LOW; **classification:** owner-decision; **owner_gated:** true.
- **Evidence:** `GOVERNANCE/PHASE_B_EVIDENCE/PHASEB_T6_FHIR_EVIDENCE.md:46-49` — router not imported/registered in `factory.py` or `main.py`; `:84-88,132-134,160-163` — `X-GULA-Principal` header is synthetic and spoofable if activated; `backend/app/factory.py` has no `fhir_http` import/reference (verified by grep); only `capabilities.fhir_interoperability` is mounted at `:656-658`; `backend/tests/health_core/test_quality_review_static.py:30,407,410-418` — WS-E guard with `FINAL_DECISION.md` MD5 `effdfeaf10234678d83b2668c4489552` verified matching and no HTTP/DDL artifacts in health_core.
- **Reproduction:** grep `fhir_http` in `factory.py`/`main.py` → no hits; `md5sum GOVERNANCE/FINAL_DECISION.md` matches the guard constant; AST guard conditions satisfied. **Falsification:** show a factory `include_router` for `fhir_http` (none) or a modified guard constant/MD5 mismatch (none).
- **Root cause:** interim design uses a test-only header principal pending a real identity/authz boundary (D-020 owner-gated).
- **Impact:** currently zero runtime exposure; if mounted before replacing the synthetic principal, any caller setting headers can impersonate a tenant/facility principal and access FHIR resources.
- **Remediation:** keep non-activated (MP-001/ODR posture respected); add a CI guard asserting no `fhir_http` import in `factory.py`/`main.py`; require a real signed-token boundary and D-020 ruling before activation.
- **Alternatives:** (1) keep dormant + CI guard (recommended); (2) replace header principal with canonical auth then activate (owner-gated, D-020); (3) delete the router (destroys a strategic dormant asset — not permitted).

---

## 5. Verdict and residual risk

1. **HOLD stands.** AUD-API-002 shows the advertised OAuth2 flow is end-to-end non-functional; AUD-API-001 shows the standards-conformance endpoint always 500s; AUD-API-006/008 show active FHIR/terminology/DICOM claims are not backed by validation.
2. **No release assurance awarded.** No runtime HTTP, DB, or network verification was permitted; nothing here is `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`.
3. **No protected state change.** D-020/D-021, ODR-001…004, MP-001, ADR-A…J, AUD-02/07/16 and the sibling repository are untouched; T6 remains dormant and WS-E holds.
4. **Top API material findings:** AUD-API-002 (OAuth2 tokens unusable by platform API), AUD-API-001 (`GET /integration/standards` deterministic 500), AUD-API-006 (active FHIR router accepts arbitrary JSON and returns non-FHIR errors).
5. **Next owner actions (not performed here):** decide OAuth2's role and unify token semantics; fix the standards endpoint against real accessors; decide whether to enforce or relabel standards conformance; keep T6 dormant behind a CI guard until D-020.

---

## 6. Artifact control statement

The only files created by this audit are:

- `GOVERNANCE/ADVERSARIAL_ASSURANCE/FINDINGS_A4_DATA_API.json`
- `GOVERNANCE/ADVERSARIAL_ASSURANCE/DATABASE_INTEGRITY_REPORT.md`
- `GOVERNANCE/ADVERSARIAL_ASSURANCE/API_AND_INTEROPERABILITY_AUDIT.md`

No pre-existing file, git index, configuration, database, server, network state, or sibling repository was modified. No secret, credential, or patient datum is included; all reproduction designs are synthetic or static.
