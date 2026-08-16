# GULA — P0 Identity & Account Lifecycle — Command 01
## Authoritative Audit + Safe Remediation + Quality Hardening

**تاريخ التنفيذ:** 16 أغسطس 2026

**الفرع:** `chore/security-ddos-hardening-clean`

**Commit الناتج:** `edd0e1c1` — `security: harden identity login and session scope`

**PR:** [#226](https://github.com/samertts/gula-platform/pull/226)

> **Final Gate:** `PARTIALLY_REMEDIATED`
>
> أُصلحت أربع مشكلات مؤكدة بإصلاحات صغيرة قابلة للمراجعة، وأضيفت اختبارات regression، ونجحت اختبارات Backend الكاملة. بقيت فجوة معمارية عالية الأهمية بين legacy authentication وNIAM canonical routes، إضافة إلى mismatch أوسع بين async identity routes وsync `get_db`. معالجة هذه الفجوة تتطلب خطة ترحيل وتوافق API وموافقة على تغيير معماري أمني؛ لذلك لم تُنفذ تخمينياً.

لم يُنفذ merge أو force-push أو history rewrite أو production deployment أو تعديل Production Database أو تفعيل Public Registration/National Identity/OCR/NFC/Biometrics أو أي تغيير حكومي/قانوني. لم يبدأ Command 02 تلقائياً.

## 1. Baseline الفعلي

تم تثبيت الحالة من Git والاختبارات الحالية، لا من التقارير القديمة فقط.

| Item | Current evidence |
|---|---|
| HEAD before remediation | `88d94b2b` — Command 08 final QA report |
| HEAD after remediation | `edd0e1c1` |
| Branch | `chore/security-ddos-hardening-clean` |
| Main remote | `1e07b8d677c5f7c94d0fb387937eff959af9589d` |
| PR #226 | `OPEN`, `UNSTABLE`, no recorded review decision |
| Working tree | Clean after commit |
| Local backend environment | Python 3.12.3, project `.venv`, SQLite test fixtures |
| Local frontend environment | Node/npm/pnpm, Vite, Playwright |
| Production DB | Not contacted |
| Vercel/Railway | Read-only evidence only; current production closure not established |

كانت جميع GitHub workflow failures الأخيرة على commit `88d94b2b` ذات `steps: []` وrunner metadata غير صالحة؛ لذلك صُنفت infrastructure failure لا code assertion failure. لم تُعاد محاولة تجاوزها أو إخفائها.

## 2. Findings Matrix

| ID | Finding | Severity | Status | Human approval |
|---|---|---:|---|---|
| IAM-01 | Permanent/manual locked account كان يُفتح تلقائياً بمحاولة login | P1 | **REMEDIATED** | لا |
| IAM-02 | Canonical NIAM account lookup لم يكن يشمل phone | P2 | **REMEDIATED** | لا |
| IAM-03 | Canonical NIAM login لم يطبّع phone/email قبل lookup | P2 | **REMEDIATED** | لا |
| IAM-04 | NIAM login كان يثق في `ip_address` و`user_agent` القادمين من query | P1 | **REMEDIATED** | لا |
| IAM-05 | NIAM auth logout لم يكن account-scoped | P1 | **REMEDIATED** | لا |
| IAM-06 | Frontend يستخدم legacy `/login`, `/session`, `/auth/refresh` بينما NIAM canonical تحت `/niam/auth/*` | P1 | **BLOCKED / UNRESOLVED** | `HUMAN_APPROVAL_REQUIRED` |
| IAM-07 | كثير من async NIAM routes تعتمد `AsyncSession = Depends(get_db)` مع `get_db` synchronous | P1 | **BLOCKED / UNRESOLVED** | `HUMAN_APPROVAL_REQUIRED` |
| IAM-08 | Legacy `LabUser/User` وNIAM `Account` models/routes response contracts متوازية | P1 | **PARTIALLY_REMEDIATED** | `HUMAN_APPROVAL_REQUIRED` |
| IAM-09 | Current-head CI/CodeQL/Preview Deploy infrastructure failures | P1 | **BLOCKED / UNVERIFIED** | Owner/infrastructure approval |
| IAM-10 | Full Ruff/MyPy/dependency tooling debt خارج diff | P2/P4 | **PARTIALLY_REMEDIATED** | لا؛ يحتاج wave منفصلة |
| IAM-11 | PostgreSQL migration/rollback وreal-device parity | P1/P4 | **UNVERIFIED** | Environment/release-owner approval |

## 3. Safe Remediation Evidence

### IAM-01 — Permanent lock bypass

**Before.** `AccountService.authenticate` كان يرى `account.is_locked` أو `status=locked`، ثم إذا كان `locked_until` فارغاً لا يرفض؛ بل ينتقل إلى `active` ويصفر failed attempts قبل اكتمال login. Reproduction محلي أثبت أن wrong password أعاد `None` لكن غيّر الحالة من `locked` إلى `active`.

**Root cause.** الخلط بين timed lockout المنتهي وmanual/permanent lock؛ الشرط القديم لم يميز `locked_until is None`.

**Impact.** محاولة unauthenticated واحدة كانت تستطيع إزالة manual lock، مما يضعف account lifecycle وlockout integrity.

**Fix.** إذا كان lock بلا expiry يُرفض login ولا تتغير الحالة. يسمح auto-unlock فقط لـtimed lockout انتهت مدته، ثم يعيد transition القانوني إلى active.

**Regression/security verification.** أُضيف `test_permanent_locked_account_is_not_unlocked_by_login_attempt`، ونجح ضمن regression suite. نجحت أيضاً refresh rotation/replay وaccount lifecycle tests.

**Regression risk.** منخفض؛ الإصلاح يقيّد transition غير القانوني فقط ولا يغير شكل response أو token contract.

### IAM-02/IAM-03 — Canonical phone/email login

**Before.** `AccountRepository.find_by_login` كان يبحث في email وusername فقط، رغم أن Account model وواجهة login يدعمان phone. كما أن `AccountService.authenticate` كان يمرر login كما هو، فلا يطابق phone الذي حفظه `create_account` بعد إزالة المسافات.

**Root cause.** عدم توحيد identifier normalization بين creation وauthentication، ونقص phone predicate في canonical repository.

**Impact.** حساب NIAM المنشأ برقم هاتف قد يفشل في canonical login، خصوصاً مع تنسيق المسافات الظاهر في واجهة الهاتف.

**Fix.** أضيف phone إلى OR predicate، ويطبّع authenticate email إلى lowercase وphone/identifier إلى صيغة بلا مسافات قبل lookup.

**Regression/security verification.** أُضيف `test_find_by_login_includes_email_username_and_phone_predicates` و`test_authenticate_normalizes_phone_login_before_lookup`. نجحت الاختبارات.

**Regression risk.** منخفض؛ email/username predicates بقيت كما هي، ولا توجد migration.

### IAM-04 — Request-derived session metadata

**Before.** `/niam/auth/login` كان يقبل `ip_address` و`user_agent` كـquery parameters ويمررهما إلى session creation.

**Root cause.** الخلط بين API compatibility parameters وtrusted server metadata.

**Impact.** يستطيع client إرسال metadata مضللة إلى session/audit records، ما يضعف التحقيقات الأمنية ودقة session attribution.

**Fix.** بقيت parameters اختيارية للتوافق فقط، لكن route يتجاهلها ويستعمل `get_client_ip(request)` و`request.headers["user-agent"]`. `get_client_ip` يطبق private-proxy trust policy الموجودة.

**Regression/security verification.** أُضيف `test_niam_login_uses_request_metadata_not_query_values`، ونجح مع Bandit targeted.

**Regression risk.** منخفض؛ لم يتغير request أو response schema، لكن metadata أصبحت server-authoritative كما ينبغي.

### IAM-05 — Account-scoped NIAM logout

**Before.** `AuthenticationService.logout(session_uuid)` كان ينهي أي session UUID موجوداً، و`/niam/auth/logout` لم يفرض actor ownership.

**Root cause.** session termination service لم يتلق account scope من authorization context.

**Impact.** knowledge of a foreign UUID كان كافياً نظرياً لطلب termination على session account آخر.

**Fix.** `AuthenticationService.logout` يقبل `account_id` اختيارياً ويعيد `False` عند عدم التطابق. `/niam/auth/logout` يطلب `get_current_niam_actor_sync` ويمرر `actor.account.id`، ويرفض foreign session بـ403.

**Regression/security verification.** أُضيف `test_niam_logout_is_account_scoped`، مع وجود canonical session ownership tests سابقة. نجحت الاختبارات.

**Regression risk.** منخفض؛ استدعاءات داخلية قديمة بلا account scope تبقى متوافقة، بينما endpoint الآمن يفرض scope.

### IAM-06/IAM-07/IAM-08 — Architecture drift not guessed away

**Current evidence.** Frontend `authApi` ما زال يستعمل `/login`, `/logout`, `/session`، وmobile refresh يستعمل `/auth/refresh`. هذه endpoints تعود إلى `backend/app/routes/login.py` و`backend/app/routes/mobile.py` التي تعمل على legacy `LabUser/User`. في المقابل، NIAM router له prefix `/niam` ويعرض canonical `/niam/auth/login`, `/niam/auth/refresh`, `/niam/auth/logout` ويعمل على `Account/UserSession`.

**Additional mismatch.** عدد كبير من identity routes و`get_current_niam_actor` يعلن `AsyncSession = Depends(get_db)`، بينما `get_db` في `backend/app/database.py` synchronous SQLAlchemy `Session`. أُصلح هذا mismatch في auth endpoints المحددة باستخدام `SyncSessionAsyncFacade`، لكن لا يجوز ادعاء أن كل identity async route أصبحت production-ready بعد ذلك الإصلاح الجزئي.

**Impact.** المسار الذي تختبره Frontend mocks ليس بالضرورة المسار canonical الذي سيعمل على backend حي. الانتقال غير المنسق قد يكسر email/phone response shape، cookies، mobile secure storage، workspace bootstrap، memberships، audit، وlegacy clinical integrations.

**Decision.** هذا تغيير **Security Architecture/API Migration** وليس إصلاحاً تخمينياً صغيراً. لم أقم بإعادة توجيه Frontend إلى `/niam/auth/*`، ولم أحذف legacy routes، ولم أنشئ duplicate Account/Person models، ولم أضيف fallback يتجاوز NIAM. الحالة `HUMAN_APPROVAL_REQUIRED` حتى تُعتمد خطة migration على بيئة Staging مع compatibility contract واختبارات cross-platform.

## 4. Testing and Verification

| Check | Result | Status |
|---|---:|---|
| Targeted identity/auth regression after all fixes | 21 passed | **PASS** |
| Backend full suite after final fixes | 2673 passed, 4 skipped, 252 warnings، 313.85s | **PASS** |
| Frontend typecheck/lint/unit/build/bundle/E2E | typecheck/lint/build/bundle PASS؛ 61 unit tests و53/53 E2E | **PASS محلياً** |
| Targeted Ruff on changed production files and new tests | PASS | **PASS** |
| Ruff format on new tests | PASS | **PASS** |
| Targeted Bandit identity/auth scope | no Medium/High findings | **PASS للنطاق** |
| Full Ruff/MyPy | legacy debt remains؛ MyPy executable unavailable في final sandbox check | **PARTIAL** |
| Migration tests | included in Backend full suite and passed | **PASS محلياً** |
| PostgreSQL upgrade/downgrade | no PostgreSQL rehearsal environment | **UNVERIFIED** |
| `git diff --check` | exit 0 | **PASS** |
| Production DB/config | not contacted | **NOT PERFORMED** |
| Real Android/iOS/Desktop runtime | not available/current-head CI infrastructure blocked | **UNVERIFIED** |

Warnings التي بقيت ليست failure في الإصلاحات: Starlette/httpx deprecation، datetime.utcnow deprecation، SQLite FK cycle warning، وSentry test flush notices.

## 5. Security Verification

لم تُسجل كلمات مرور أو OTP أو tokens أو private keys في الإصلاحات أو الاختبارات الجديدة. لم يُستخدم `localStorage` لتخزين access/refresh tokens في current Frontend؛ موضع `localStorage.removeItem("access_token")` الموجود هو E2E cleanup وليس storage path.

نجحت اختبارات default-deny وtenant/workspace isolation وrefresh replay وsession ownership وaudit contracts السابقة، إضافة إلى regression tests الجديدة. بقيت route split بين legacy وNIAM عائقاً تشغيلياً/معمارياً يجب إغلاقه قبل إعلان identity lifecycle complete.

## 6. Performance and Data Integrity

الإصلاحات لا تضيف caching ولا تغيّر query plans ولا تخفف authorization. `find_by_login` أضاف predicate فقط، وlock fix لا يضيف database write عند manual lock، وlogout ownership يقرأ session ثم يوقفها داخل نفس service contract.

نجحت performance/resilience tests السابقة ضمن full suite، بما في ذلك query budgets وpagination caps وhealth checks وrate-limit/resilience smoke. لا توجد مقارنة production p50/p95/p99 ولا PostgreSQL load profile، لذلك Performance Gate خارج local evidence بقي `UNVERIFIED`.

لا توجد migration لهذه الإصلاحات. Single Alembic head والاختبارات المحلية ناجحة، لكن existing-data compatibility وrollback على PostgreSQL لم يُثبتا.

## 7. UX, Accessibility, Localization, Cross-Platform

لم تُعدّل واجهة Frontend لأن findings المعالجة Backend-local ولا يجوز تغيير contract UI أثناء migration architectural غير معتمدة. Web/PWA quality وE2E local ناجحة. Mobile/Desktop current-head runtime وdeep-link invocation وMFA/passkey ceremony وdevice accessibility بقيت `UNVERIFIED` وفق القيود السابقة.

الـlogin UI ما زال يعرض email-or-phone، وأصبح canonical AccountService يدعم phone predicate وnormalization. لكن Frontend production caller ما زال legacy endpoint، ولذلك لا يصح اعتبار canonical NIAM phone path مستخدماً في الإنتاج.

## 8. Remaining Debt by Priority

### Critical / P0 Remaining

لا يوجد Critical/High bypass مثبت في الإصلاحات المحلية. لكن لا يجوز إعلان P0 closure الكامل قبل حل legacy-vs-NIAM route split والتحقق من أن كل production callers يمرون عبر server-authoritative canonical actor/session context.

### P1 Remaining

تبقى canonical route migration، async/sync identity dependency alignment، existing production runtime/flags/database evidence، current-head CI/CodeQL/Preview infrastructure، وfull operational lifecycle E2E على Staging.

### P2/P4 Remaining

تبقى full Ruff/MyPy cleanup، dependency/secret scanners غير المتاحة في sandbox، PostgreSQL migration/rollback rehearsal، real-device parity، Persian resource independence، WebAuthn/passkey ceremony، and performance p95/p99 profiles.

## 9. Human Approval Gate

القضايا التالية تحمل `HUMAN_APPROVAL_REQUIRED` ولا تنفذ آلياً:

| Approval | Reason |
|---|---|
| Security architecture migration from legacy auth to NIAM | تغيير source of truth وsession/cookie/token contracts |
| Breaking/compatibility API decision | اختلاف `/login` مقابل `/niam/auth/login` وresponse shapes |
| Production flag/runtime verification or change | لا Production mutation ضمن هذا الأمر |
| PostgreSQL migration/rollback rehearsal | يحتاج بيئة Staging وبيانات synthetic وموافقة release owner |
| National ID/OCR/NFC/Biometrics activation | Legal/government/security boundary |
| Merge or production deploy | PR #226 ما زال يحتاج review/checks مستقلة |

## 10. Final Decision

```text
Command 01 = PARTIALLY_REMEDIATED
SAFE_LOCAL_FIXES = 5
CRITICAL_SECURITY_BYPASS_FOUND = NO (local evidence)
P1_ARCHITECTURE_GAP = YES
PRODUCTION_CHANGE = NOT PERFORMED
HUMAN_APPROVAL_REQUIRED = YES
COMMAND 02 = NOT_STARTED / NOT_AUTHORIZED
```

**Next Exact Action:** إعداد migration design معتمد يحدد canonical source of truth، compatibility bridge، cookie/token policy، sync/async database boundary، workspace bootstrap، mobile secure-storage contract، audit continuity، وrollback. بعدها تُنفذ rehearsal كاملة على Staging PostgreSQL/Redis ببيانات synthetic، ثم تُعاد Frontend/native/CodeQL/CI checks على نفس commit قبل أي merge أو deployment.

## References

[1]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/app/identity/services/account_service.py "AccountService lock and login normalization"
[2]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/app/identity/repositories/account_repository.py "AccountRepository login predicates"
[3]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/app/identity/api/auth.py "NIAM authentication API"
[4]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/app/identity/services/authentication_service.py "AuthenticationService session lifecycle"
[5]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/app/identity/api/router.py "NIAM router prefix and route composition"
[6]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/app/routes/login.py "Legacy login/session route"
[7]: https://github.com/samertts/gula-platform/blob/edd0e1c1/frontend-v3/src/api/endpoints.ts "Frontend auth endpoint contract"
[8]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/app/database.py "Synchronous get_db dependency"
[9]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/tests/identity/test_auth_api_security.py "NIAM auth security regression tests"
[10]: https://github.com/samertts/gula-platform/blob/edd0e1c1/backend/tests/test_identity_authentication_security.py "Identity authentication regression tests"
