# GULA — P0 Identity & Account Lifecycle — Command 02
## Account Lifecycle Hardening + Safe Remediation

**تاريخ التنفيذ:** 16 أغسطس 2026

**الفرع المحلي:** `chore/security-ddos-hardening-clean`

**آخر commit محلي:** `055078ce` — `security: harden account lifecycle boundaries`

**آخر commit على remote قبل هذا الأمر:** `e4fe5d1b`

> **Final Status:** `ACCOUNT_LIFECYCLE_PARTIAL`
>
> تم تنفيذ الإصلاحات الآمنة المؤكدة في حدود العقود الحالية، وإضافة regression coverage، وتشغيل Backend وFrontend quality gates محلياً. لم تُنفذ عملية approval/activation الكاملة لأن التنفيذ الفعلي لها غير موجود في canonical NIAM API، ولأن إنشائها يتطلب قراراً معمارياً ومخطط بيانات وصلاحيات إدارية معتمدة. لم يتم تعديل Production ولم يبدأ Command 03.

## 1. Baseline وProduction Safety

تم تتبع التنفيذ الفعلي من المصدر والاختبارات، لا الاعتماد على أسماء الملفات أو التقارير السابقة فقط.

| المجال | الدليل والنتيجة |
|---|---|
| Branch | `chore/security-ddos-hardening-clean` |
| Local HEAD | `055078ce` |
| Remote branch | ما زال عند `e4fe5d1b` لأن GitHub authentication في الجلسة الحالية غير صالح |
| Working tree | نظيف بعد commit التقرير المحلي |
| Public self-registration | **OFF** افتراضياً عبر `PUBLIC_SELF_REGISTRATION_ENABLED=false` |
| Account Request | intake فقط، `202 Accepted`، ولا ينشئ أو يفعّل حساباً |
| Direct account create/lock/unlock | **410 Gone** وfail-closed حتى تتوفر صلاحية إدارية محكومة |
| Alembic | **Single head PASS:** `20260815_0022` |
| New migration | لا توجد؛ الإصلاحات لا تتطلب تغيير schema |
| Production DB/runtime/flags | لم يتم الاتصال أو التعديل |
| Deployment/merge | لم ينفذ أي merge أو deployment |

فشلت محاولة الدفع مرتين بسبب token GitHub غير صالح، كما فشل بديل SSH لعدم وجود مفاتيح SSH موثقة وظهور `Host key verification failed`. لذلك يبقى commit `055078ce` محفوظاً محلياً فقط حتى تتم إعادة مصادقة GitHub خارج هذا التنفيذ.

## 2. Current Lifecycle Reality

الدورة canonical الحالية تتكون فعلياً من `pending_verification` و`active` و`suspended` و`locked` و`disabled` و`deactivated` على مستوى Account، بينما Account Request له حالات `pending_review` و`approved` و`rejected` و`cancelled`. توجد فجوة واضحة بين النموذج المطلوب في Command 02 وبين المسارات الفعلية: لا توجد في `account_requests.py` مسارات review/approve/reject/activate، كما أن `accounts.py` يغلق direct creation وlock/unlock بـ410.

`AccountLifecycleService` يفرض transitions deny-by-default داخل الحالات الموجودة، لكنه يسمح تاريخياً بالانتقال `pending_verification → active` لأن هذا هو العقد الذي تثبته الاختبارات الحالية. لا يجوز تحويله تلقائياً إلى سلسلة جديدة تشمل `verified`, `pending_approval`, `approved`, `rejected`, و`expired` من دون migration وتحديث callers وواجهة الإدارة وسياسة الصلاحيات.

| Lifecycle requirement | Current status | Decision |
|---|---|---|
| Request intake | **PASS** | موجود ومحصّن نسبياً |
| Verification state | **PARTIAL** | verification records موجودة، لكن ليست مرتبطة بمسار account approval كامل |
| Account creation | **PARTIAL** | service موجود وDB unique fields موجودة، لكن لا يوجد canonical request-to-account orchestration |
| Review/approval/rejection | **BLOCKED** | لا توجد canonical endpoints/service كاملة |
| Activation | **PARTIAL/BLOCKED** | transition service موجود، لكن لا توجد approval-gated activation route |
| Suspension/lock | **PARTIAL** | state service موجود؛ route الإداري المحكوم غير مكتمل |
| Reactivation | **BLOCKED** | لا يوجد governed reactivation workflow كامل |
| Deactivation | **PARTIAL** | transition موجود، لكن audit/authorization orchestration غير موحّد عبر كل المسارات |

## 3. Remediations Implemented

### IAM-02 — Refresh/session authorization for locked accounts

**Problem.** كان `AuthenticationService.refresh_session` يتحقق من `is_active` فقط؛ كما أن async `get_current_niam_actor` لم يكن يضيف `Account.is_locked = false` إلى query، مما يسمح نظرياً ببقاء session context لحساب مقفل إذا بقي active.

**Root cause.** اختلاف شروط status بين refresh path وcanonical actor resolution.

**Fix.** يرفض refresh الآن الحساب الذي ليس `active` أو ليس `is_active` أو `is_locked`. وأضيف شرط `Account.is_locked.is_(False)` إلى async actor query.

**Security verification.** أضيف `test_refresh_is_rejected_for_locked_account_without_blacklisting`، وأضيف assertion على compiled actor query لوجود شرط `is_locked`.

**Regression result.** اختبارات session/workspace/auth نجحت، ولم يُجرَ blacklist أو session rotation للحساب المقفل.

### IAM-03 — Duplicate account creation transaction safety

**Problem.** Account fields email/phone/username لها unique constraints، لكن `AccountService.create_account` كان يترك `IntegrityError` الخام، وقد يترك transaction في حالة failed ويكشف تفاصيل DB للطبقة الأعلى.

**Root cause.** عدم وجود domain-level handling لسباق الإنشاء أو retry.

**Fix.** أضيف `DuplicateAccountError`، مع rollback sync/async عند `IntegrityError`. تُصنّف أخطاء unique فقط كـduplicate، بينما تعاد أخطاء FK/constraint الأخرى بعد rollback. أضيف أيضاً تحقق fail-closed من `identity_id`.

**Security/data verification.** لا يتم إنشاء Account ثانٍ، ولا تُمنح صلاحية، ولا يمر partial object بعد فشل unique insert.

**Regression result.** `test_duplicate_account_creation_rolls_back_and_returns_domain_error` نجح ضمن suite.

### IAM-04 — Account Request idempotency race

**Problem.** كان المسار يفحص `Idempotency-Key` ثم ينشئ السجل؛ retry المتزامن قد يصطدم بـunique constraint ويترك transaction مكسورة بدلاً من إعادة السجل الموجود.

**Root cause.** نافذة check-then-insert بلا recovery بعد unique collision.

**Fix.** عند `IntegrityError` يحدث rollback، ثم إعادة قراءة سجل `idempotency_key_hash`. إذا وجد يعاد السجل الموجود من دون audit event ثانٍ أو سجل جديد.

**Regression result.** `test_submit_retries_idempotency_race_without_duplicate_or_audit` نجح.

> هذا الإصلاح يغلق race الخاص **بنفس idempotency key**. منع concurrent requests مختلفة المفاتيح لنفس جهة الاتصال على مستوى عدة workers يحتاج unique/index policy أو database locking مع migration؛ لم يُخترع هذا السلوك في غياب Staging PostgreSQL وقرار retention/re-submission.

### IAM-05 — Idempotency key misuse

**Problem.** كان استعمال المفتاح نفسه مع payload مختلف يعيد الطلب السابق وكأنه retry صحيح.

**Root cause.** عدم مقارنة `request_fingerprint` عند existing key.

**Fix.** أضيف `IdempotencyConflictError`. retry المطابق يبقى idempotent، أما إعادة استخدام المفتاح مع payload مختلف فتُرفض داخلياً، ويعيد API `409 Conflict` برسالة عامة لا تكشف بيانات الطلب السابق.

**Regression result.** `test_submit_rejects_idempotency_key_reuse_with_different_payload` نجح، كما بقيت public response redacted.

### IAM-06 — Trusted client IP for Account Request

**Problem.** كان Account Request يسجل `request.client.host` مباشرة، بخلاف trusted proxy policy المستخدمة في auth.

**Root cause.** عدم توحيد مصدر client IP بين account intake وauth.

**Fix.** يستعمل endpoint الآن `get_client_ip(request)`، الذي لا يثق بـforwarded headers إلا عند اتصال proxy خاص موثوق.

**Regression result.** `test_account_request_uses_trusted_client_ip` نجح.

### IAM-07 — Frontend/Backend account-request contract

**Problem.** Frontend كان يعلن `requested_account_type` كـ`human | organization | service` ويعرض خيار المؤسسة، بينما Backend canonical intake يقبل human فقط.

**Root cause.** توسع UI contract دون backend workflow مؤسسي مطابق.

**Fix.** حُصر TypeScript contract في `human`، وثُبّت RegisterPage على human-only، واستُبدل selector القابل للإرسال برسالة واضحة. بقيت بطاقة المؤسسة كتوضيح أن لها مسار اعتماد منفصل ولا تُنشأ من public request form.

**UX/security result.** لا يمكن للواجهة إرسال account type سيرفضه Backend، ولا يُفهم من الشاشة أن Public Registration أو institution account creation متاحان.

## 4. Verification Matrix

| Gate | Result | Classification |
|---|---:|---|
| Backend full suite | **2678 passed, 4 skipped, 252 warnings** في 309.72s | **PASS** |
| Command 02 targeted identity/session/account suite | **32 passed** | **PASS** |
| Frontend typecheck | exit 0 | **PASS** |
| Frontend lint | exit 0 | **PASS** |
| Frontend unit | **61 tests / 17 files passed** | **PASS** |
| Frontend production build/PWA | **PASS**, 190 precache entries | **PASS** |
| Bundle budget | total **1,497,928 bytes**, entry JS **344,698**, CSS **138,528**, violations **0** | **PASS** |
| Playwright E2E | **53/53 passed** محلياً | **PASS محلياً** |
| Targeted Ruff | exit 0 | **PASS** |
| Targeted Bandit identity/account scope | exit 0، دون Medium/High findings | **PASS للنطاق** |
| `git diff --check` | exit 0 | **PASS** |
| Alembic heads | single head `20260815_0022` | **PASS** |
| PostgreSQL upgrade/downgrade rehearsal | لا توجد PostgreSQL/Staging environment مناسبة | **UNVERIFIED** |
| Flutter Analyze/Test/build | Flutter غير متاح محلياً | **NOT_BUILT / UNVERIFIED** |
| Current-head GitHub CI | لا توجد runs جديدة للـlocal commit؛ الدفع محجوب بالمصادقة | **BLOCKED** |

Warnings في Backend ليست regressions في هذا الأمر، وتشمل deprecations في Starlette/httpx و`datetime.utcnow` وSQLite FK cycle test warning وSentry flush notices.

## 5. Security and Data Integrity Assessment

نجحت الاختبارات المرتبطة بـdefault-deny، tenant/workspace isolation، session ownership، refresh replay، rate limit، public account request redaction، وdirect account mutation fail-closed. لا تسجل الإصلاحات passwords أو OTP أو access/refresh tokens أو private secrets.

لم يُضف caching لأي security state. لم تُضف migration، ولم تُمسح بيانات، ولم تتغير membership rows أو audit history. الإصلاحات transaction-local، وunique failures تعود بعد rollback بدلاً من مواصلة transaction غير صالحة.

يبقى cross-process duplicate suppression للطلبات ذات **مفاتيح مختلفة** غير مثبت. كما يبقى legacy `LabUser/User` auth منفصلاً عن NIAM `Account/UserSession`، وهو ما يمنع إعلان lifecycle موحد عبر كل production callers.

## 6. Frontend, PWA, Mobile/Desktop

Web/PWA: **PASS محلياً**؛ RegisterPage الآن يعكس human-only review intake، وerror mapping الحالي يغطي 401 و403 و409 و429 و5xx وoffline برسائل آمنة.

Android/iOS/Flutter/Desktop: **UNVERIFIED / NOT_BUILT في هذه الدورة** لأن Flutter SDK غير متاح محلياً ولم توجد CI runs جديدة على commit `055078ce` بسبب فشل GitHub authentication. لم تُنفذ إعادة بناء منصات غير جاهزة، ولم تُعتبر نتيجة Web دليلاً على device runtime parity.

## 7. Remaining P0/P1/P4 Gates

| Gate | Status | Required next action |
|---|---|---|
| Canonical review/approve/reject/activate workflow | **BLOCKED** | اعتماد API/state/migration/permission design ثم تنفيذها على Staging |
| Full state machine (`verified`, `pending_approval`, `approved`, `rejected`, `expired`) | **BLOCKED** | قرار compatibility ومخطط migration قبل تغيير enum/status contracts |
| Legacy vs NIAM auth unification | **HUMAN_APPROVAL_REQUIRED** | compatibility bridge أو coordinated cutover مع Web/PWA/Mobile/Desktop |
| Async identity routes using sync `get_db` | **PARTIAL** | إكمال facade/DB boundary audit route-by-route على Staging |
| Cross-worker duplicate requests with different idempotency keys | **UNVERIFIED** | PostgreSQL concurrency rehearsal وunique/index policy |
| PostgreSQL migrations/rollback | **UNVERIFIED** | Synthetic Staging DB وupgrade/downgrade rehearsal |
| Flutter/native CI and device runtime | **BLOCKED** | إعادة مصادقة GitHub ثم تشغيل native workflows على نفس commit |
| CodeQL/production deployment checks | **BLOCKED/UNVERIFIED** | إصلاح GitHub credentials/permissions ثم إعادة checks؛ لا bypass |

## 8. Final Decision and Stop Conditions

```text
ACCOUNT_LIFECYCLE = PARTIAL
SAFE_REMEDIATIONS = 6
CRITICAL_LOCAL_BYPASS_FOUND = NO
PUBLIC_SELF_REGISTRATION = OFF
PRODUCTION_CHANGE = NOT PERFORMED
MIGRATION_ADDED = NO
POSTGRES_RUNTIME = UNVERIFIED
FLUTTER_RUNTIME = NOT_BUILT / UNVERIFIED
REMOTE_PUSH = BLOCKED_BY_INVALID_GITHUB_AUTH
COMMAND_03 = NOT_STARTED / NOT_AUTHORIZED
```

لا توجد حالياً قرينة على data corruption أو cross-tenant leakage ناتجة عن الإصلاحات الجديدة. لكن لا يجوز إعلان `ACCOUNT_LIFECYCLE_REMEDIATED` قبل تنفيذ approval/activation orchestration، وتوحيد source of truth، وإثبات PostgreSQL وCI/native runtime. لذلك القرار الآمن هو `ACCOUNT_LIFECYCLE_PARTIAL`، وليس merge/release approval.

**Next Exact Action:** إعادة مصادقة GitHub في جلسة موثوقة ثم دفع commit `055078ce`. بعد ذلك يجب إعداد تصميم معتمد لـAccount Request review وverification وapproval وactivation وreactivation، مع صلاحية إدارية server-side، audit events كاملة، migration/rollback plan، وStaging PostgreSQL/Redis concurrency rehearsal. لا يبدأ Command 03 تلقائياً.

## References

[1]: https://github.com/samertts/gula-platform/blob/055078ce/backend/app/identity/models/account.py "Canonical Account model and statuses"
[2]: https://github.com/samertts/gula-platform/blob/055078ce/backend/app/identity/services/account_lifecycle_service.py "Account lifecycle transition matrix"
[3]: https://github.com/samertts/gula-platform/blob/055078ce/backend/app/identity/services/account_request_service.py "Account request intake, idempotency, and redaction"
[4]: https://github.com/samertts/gula-platform/blob/055078ce/backend/app/identity/api/account_requests.py "Account request API contract"
[5]: https://github.com/samertts/gula-platform/blob/055078ce/backend/app/identity/api/accounts.py "Fail-closed direct account mutations"
[6]: https://github.com/samertts/gula-platform/blob/055078ce/backend/app/identity/services/authentication_service.py "Refresh/session account authorization"
[7]: https://github.com/samertts/gula-platform/blob/055078ce/backend/app/identity/api/workspaces.py "Canonical NIAM actor and workspace authorization"
[8]: https://github.com/samertts/gula-platform/blob/055078ce/frontend-v3/src/api/endpoints.ts "Frontend account-request contract"
[9]: https://github.com/samertts/gula-platform/blob/055078ce/frontend-v3/src/pages/auth/RegisterPage.tsx "Frontend account-request UX"
[10]: https://github.com/samertts/gula-platform/blob/055078ce/backend/tests/identity/test_account_request_security.py "Account request security regression tests"
[11]: https://github.com/samertts/gula-platform/blob/055078ce/backend/tests/identity/test_auth_session_security_phase2.py "Refresh/session security regression tests"
