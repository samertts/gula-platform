# GULA — P0 Identity & Account Lifecycle — Command 04

**العنوان:** Authentication + Session Management
**التاريخ:** 16 آب 2026
**الفرع:** `security/p0-bootstrap-alembic`
**النقطة الأساسية قبل التنفيذ:** `f39ed730`
**رأس Alembic بعد التنفيذ:** `20260815_0025`
**القرار النهائي:** `AUTHENTICATION_PARTIAL` مع `SAFE_STOP` قبل Command 05

## 1. الملخص التنفيذي

تم تنفيذ بنود Command 04 القابلة للإثبات محلياً باستخدام مكونات NIAM الموجودة، دون إعادة بناء الهوية أو تفعيل production أو government identity. شمل التنفيذ إصلاح ربط `jti` بين JWT وسجل `UserSession`، إضافة lineage دائم لعائلة Refresh Tokens، اكتشاف replay وإبطال العائلة كاملة، إضافة مهلة idle وabsolute للجلسة، تقوية NiamActor وWorkspace Context، وتأمين مسارات logout وsession management ضد cross-account access.

كما أضيفت عقود Frontend typed لمسارات NIAM auth والجلسات، مع إبقاء حاجز الكتابة والقراءة server-authoritative وعدم تخزين session secrets في `localStorage` أو `sessionStorage`. لم تُستبدل منظومة المصادقة legacy في الواجهة لأن المسارات السريرية الحالية تعتمد عقد `LabUser/User` القديم، ولا يوجد عقد migration معتمد يضمن parity مع Account/UserSession.

> **النتيجة ليست `AUTHENTICATION_COMPLETE`** لأن المسار canonical NIAM HTTP يستخدم حالياً خدمة async مع dependency قاعدة بيانات عامة sync، ولم تتوفر بيئة staging/production تثبت هذا الربط runtime. كما أن Web/legacy وNIAM ما زالا مسارين متوازيين، وAndroid وFlutter وiOS لم تُثبت parity الخاصة بها في هذه البيئة.

## 2. Authentication Inventory

| العنصر | التصنيف | النتيجة الفعلية |
|---|---|---|
| Legacy `/login` | `PARTIAL` | مصادقة `LabUser/User` مع dummy hash، rate limiting، verification gate، MFA للـprivileged roles، وHttpOnly/Secure/SameSite cookies. لا ينشئ `niam_sessions`. |
| Legacy `/auth/refresh` | `PARTIAL` | يقبل body أو HttpOnly cookie ويعيد تدوير JWT مع blacklist؛ لا يرتبط بسجل UserSession أو refresh family canonical. |
| Legacy `/logout` | `PARTIAL` | يبطل access/refresh JTIs ويرفع `perm_version`، لكنه لا يميز current session عن all sessions ويؤثر في كل tokens للحساب legacy. |
| Legacy `/session` | `PARTIAL` | يعيد هوية المستخدم legacy فقط ولا يعيد canonical NiamActor أو Workspace Context. |
| NIAM `/niam/auth/login` | `PARTIAL/UNVERIFIED` | AuthenticationService ينفذ Account status/password gate وينشئ UserSession وcookies؛ runtime HTTP يحتاج AsyncSession provider معتمد. |
| NIAM `/niam/auth/refresh` | `PARTIAL` | body/query/cookie contract، access/refresh rotation، expiry/idle checks، lineage، replay family invalidation، وcookie replacement. |
| NIAM `/niam/auth/logout` | `IMPLEMENTED` على مستوى العقد والخدمة | يتطلب NiamActor، يثبت ownership، يبطل access/refresh tokens، ينهي الصف، يمسح cookies، ويسجل audit event. Runtime production غير متحقق. |
| NIAM `/niam/auth/logout-all` | `IMPLEMENTED` على مستوى العقد والخدمة | يعدد جلسات الحساب، يبطل token classes، ينهي كل الجلسات، ويسجل scope/count. Runtime production غير متحقق. |
| NIAM Sessions API | `PARTIAL` | list/terminate/terminate-all أصبح actor-guarded وaccount-owned، ولا يعيد JTIs أو secrets. لا توجد واجهة تشغيلية كاملة في الويب الحالي. |
| Secure Session ID | `IMPLEMENTED` | UUID وaccess/refresh JTI لكل UserSession، مع إصلاح مطابقة JTI الفعلية داخل JWT. |
| Expiration | `IMPLEMENTED` | Access JWT قصير؛ `expires_at` للـabsolute session/refresh lifetime. |
| Idle Timeout | `PARTIAL` | 60 دقيقة افتراضياً عبر `NIAM_SESSION_IDLE_TIMEOUT_MINUTES`، مع فحص `last_activity_at` في NiamActor وrefresh؛ يحتاج تشغيل Postgres متعدد العمال وتحقق staging. |
| Rotation | `IMPLEMENTED` على canonical service | كل refresh صالح ينهي session القديمة وينشئ session جديدة ضمن family نفسها. |
| Reuse Detection | `IMPLEMENTED` على canonical service | replay لتوكن rotated يكتشف السجل inactive ذي `refresh_rotation` وينهي العائلة كاملة مع audit. |
| Revocation | `PARTIAL` | Redis JTI blacklist وDB `is_active/terminated_at` معاً؛ الاعتماد التشغيلي على Redis متعدد العمال غير مثبت محلياً لأنه يستخدم in-memory عند غياب REDIS_URL. |
| Concurrent Sessions | `PARTIAL` | عدة جلسات مسموحة، وإدارة الجلسات موجودة؛ لا توجد policy موصولة لحد أقصى أو single-session افتراضي. |
| Device Identification | `PARTIAL` | UserSession يدعم `device_id`, IP, user-agent والـmetadata؛ canonical login الحالي لا يوثق device attestation أو trust policy كاملة. |
| CSRF | `PARTIAL/UNVERIFIED` | cookies تحمل `HttpOnly`, `Secure` عند البيئة المناسبة و`SameSite=Strict`؛ لا يوجد double-submit/anti-CSRF token مستقل مثبت لكل mutation cookie-based. |
| MFA | `PARTIAL` | TOTP/WebAuthn موجودان لإدارة MFA بعد authentication؛ privileged legacy roles لها MFA gate، لكن MFA ليست مكتملة كعامل primary داخل canonical NIAM login. |
| Passkey/WebAuthn | `PARTIAL` | management/authentication routes موجودة؛ لم تُربط كمسار login canonical يرفع Identity Assurance. |
| Rate Limiting | `PARTIAL` | login/refresh/verification مغطاة بدرجات مختلفة؛ Recovery وPasskey operations تحتاج matrix اختبار مستقل. |
| Lockout | `IMPLEMENTED` على AccountService | خمس محاولات وtemporary lock مع server-side status gate؛ policy legacy منفصلة وتحتاج توحيداً لاحقاً. |

## 3. Authentication Model Separation

تم الحفاظ على الفصل بين طبقات النموذج:

| الطبقة | المسؤولية |
|---|---|
| Identity | الشخص والهوية والسمات المرجعية. |
| Account | بيانات الدخول وحالة الحساب والـcredentials policy. |
| Authentication | قرار credential/password/MFA ورفض الحالات غير المسموحة. |
| Session | access/refresh JTIs، expiry، idle activity، device/IP/user-agent، revocation، وrefresh lineage. |
| NiamActor | ربط Account بجلسة UserSession بعد تحقق token/session/account. |
| Membership | علاقة الحساب بالمؤسسة أو المنشأة أو الصلاحية. |
| Workspace | السياق التشغيلي server-side المرتبط بالجلسة. |
| Authorization | قرار permission/policy بعد authentication، وليس جزءاً من نجاح login. |

نجاح login لا يمنح permission تلقائياً. ولا يقبل Workspace API `organization_id` أو `facility_id` أو `workspace_id` من العميل كقيم authoritative؛ يمر اختيار workspace عبر `WorkspaceService` و`WorkspaceSessionContext` المرتبط بالجلسة.

## 4. Login Flow

المسار canonical المثبت في الخدمة هو:

```text
Credentials
  → AccountService.authenticate
  → account status/lock/active gate
  → access + refresh JWT with durable JTIs
  → UserSession row
  → citizen workspace provisioning if applicable
  → HttpOnly cookie + native bearer response
  → NiamActor on protected request
  → server-side Workspace Context
  → Membership/Role/Entitlement/Policy authorization
  → Application
```

يُرفض الدخول server-side عند `pending_verification`, `suspended`, `disabled`, `deactivated`, `locked`, أو `is_active=false`. كما يستمر dummy-hash path عند login identifier غير موجود لمنع enumeration timing.

المسار legacy يبقى منفصلاً ومصنفاً `PARTIAL`، لأن تبديله قسراً كان سيكسر عقود clinical routes الحالية. لم يُنفذ fallback يرفع امتيازاً أو يتجاوز NIAM.

## 5. Session Model

أضيف إلى `niam_sessions`:

| الحقل | الغرض |
|---|---|
| `refresh_family_id` | معرف lineage دائم يجمع كل rotations لجلسة refresh واحدة. |
| `refresh_replaced_by_jti` | ربط refresh token القديم بالتوكن الذي استبدله للتحقيق في replay. |

كما تم استعمال الحقول الموجودة `started_at`, `last_activity_at`, `expires_at`, `is_active`, `terminated_at`, `termination_reason`, `device_id`, `ip_address`, `user_agent`, `auth_method`, و`mfa_used`.

تم إصلاح `backend/app/security/auth.py` بحيث يحافظ على `jti` الذي يمرره canonical AuthenticationService بدلاً من استبداله دائماً. وهذا يمنع أن يصدر JWT بـJTI مختلف عن `UserSession.token_jti`، وهي فجوة كانت تمنع NiamActor من مطابقة جلسة صحيحة.

## 6. Refresh Model and Replay Protection

يقبل NIAM refresh token من body أو query للتوافق الانتقالي أو HttpOnly cookie للويب. عند refresh صالح:

1. يُفك التوكن ويُتحقق من نوعه وJTI.
2. تُبحث الجلسة النشطة بواسطة `refresh_token_jti`.
3. يُفحص account status وactive/locked state وabsolute expiry وidle timeout.
4. يُحظر JTI القديم حتى انتهاء العمر المتبقي.
5. تُعلّم الجلسة القديمة `refresh_rotation` وتُحفظ replacement lineage.
6. تُنشأ جلسة جديدة ضمن `refresh_family_id` نفسها.
7. تُعاد access/refresh tokens وتُستبدل cookies.

عند replay لتوكن rotated، لا يُنشأ session جديد. يُكتشف السجل inactive، وتُنهى كل الجلسات النشطة في family، ويُسجل `session_reuse_detected` بنتيجة denied. لا تُحفظ قيمة التوكن أو الـsecret في audit.

## 7. Logout and Revocation Model

يدعم العقد canonical:

| العملية | التنفيذ |
|---|---|
| Current session logout | يتطلب NiamActor، يثبت session ownership، يبطل access وrefresh JTIs، ينهي DB session، يمسح cookies. |
| Logout all sessions | يتطلب NiamActor، يعدد جلسات الحساب نفسه، يبطل كل token classes، ينهي الجميع، ويعيد العدد. |
| Revoke device/session | Sessions API يسمح بإنهاء جلسة مملوكة فقط، ويمر عبر AuthenticationService حتى لا يحدث DB-only logout. |
| Security revocation | `is_active=false` وblacklist وtermination reason تعمل معاً؛ provider/incident workflow الخارجي غير مفعّل. |

المسار القديم `/logout` لا يزال global-permission-version based، ولذلك يصنف `PARTIAL` حتى يتم اعتماد migration موحد من legacy identities إلى NIAM accounts.

## 8. Workspace Context and Authorization Boundary

يستخدم `get_current_niam_actor` token payload للبحث server-side عن Account وUserSession معاً، ويشترط:

- token يحتوي `account_uuid` و`jti`.
- JTI غير موجود في blacklist.
- Account active وstatus `active` وغير locked.
- UserSession active ومطابق لـJTI.
- session ليست absolute-expired أو idle-expired.

بعد نجاح actor، يتم تحديث `last_activity_at` ويُنفذ اختيار workspace عبر `WorkspaceService`. ويستمر existing deny behavior عند اختيار workspace غير eligible. اختبارات wrong workspace وcross-account context مرت.

لا توجد قيمة client-supplied لـorganization/facility/workspace authoritative في هذا الحد. أما endpoints الأخرى خارج NIAM actor boundary فتحتاج استمرار تدقيق مستقل ولا تُعتبر مغطاة بمجرد وجود هذا dependency.

## 9. Audit Events and Privacy

تمت إضافة أو تفعيل audit events في canonical service للعناصر التالية:

```text
login_success
login_failure
session_refreshed
session_reuse_detected
logout
session_terminated
workspace_switched (existing workspace boundary)
```

تُحفظ metadata محدودة مثل scope وfamily identifier وoutcome دون password أو OTP أو access token أو refresh token أو session secret أو raw credentials. يسجل AuditService hash-chain عند توفر SQLAlchemy AsyncSession الحقيقي.

تبقى أحداث `session_created`, `refresh_failure`, `MFA change`, و`Passkey change` بحاجة إلى تغطية موحدة عبر كل adapters legacy/canonical، ولذلك لا تُصنف المنظومة audit-complete.

## 10. API Contract Changes

أُبقيت المسارات الحالية ولم تُنشأ مسارات عشوائية. أضيفت/قُويت عقود NIAM التالية تحت `/niam`:

| المسار | التغيير |
|---|---|
| `POST /niam/auth/login` | cookie-aware canonical login مع native bearer response. |
| `POST /niam/auth/refresh` | body/query/cookie input، rotation وcookie replacement. |
| `POST /niam/auth/logout` | actor-owned current-session logout مع token revocation. |
| `POST /niam/auth/logout-all` | actor-owned all-session revocation. |
| `GET /niam/sessions/account/{account_id}` | ownership check وsafe session metadata فقط. |
| `POST /niam/sessions/{session_uuid}/terminate` | account ownership وAuthenticationService revocation. |
| `POST /niam/sessions/account/{account_id}/terminate-all` | account ownership وfamily/account revocation. |

تم الحفاظ على عقد refresh القديم query/body كحل انتقالي، ولم تُعد ORM models مباشرة في responses؛ لا تُعاد JTIs أو secrets.

## 11. Frontend Status

أضيفت في `frontend-v3`:

- `niamAuthApi` typed لـlogin/refresh/logout/logout-all.
- `NiamSessionSummary` وقراءة/إنهاء جلسات NIAM في `ApiClient`.
- تحديث read/write barriers للسماح بالعقود المصنفة فقط ورفض المسارات غير المعروفة.
- اختبارات تمنع فتح endpoint غير مصنف.

بقي `AuthContext` و`LoginPage` مرتبطين بالمسار legacy `/login` و`/session` عمداً؛ لا توجد عملية تحويل صامتة إلى canonical NIAM لأن ذلك يحتاج عقد mapping رسمي بين `UserInfo` legacy و`Account/Identity/Membership`. لا تستخدم الواجهة localStorage أو sessionStorage لحفظ session secrets؛ sessionStorage محصور في demo markers وAPI mode.

صفحة `/security` الحالية ما زالت عرضاً أمنياً read-only، ولا توجد بعد صفحة تشغيلية كاملة `/sessions` مرتبطة بحساب NIAM canonical. لذلك تصنيف Frontend هو `PARTIAL` وليس `COMPLETE`.

## 12. Cross-platform Status

| المنصة | التصنيف | الدليل |
|---|---|---|
| Web/PWA | `PARTIAL` | typed contracts وcookie transport و401 retry وbarriers و50 اختباراً ناجحاً؛ AuthContext ما زال legacy. |
| Android | `UNVERIFIED` | Android SDK غير متاح في البيئة، ولم تُشغل compile/instrumentation tests لـCommand 04. |
| Flutter/Desktop | `UNVERIFIED` | Flutter SDK غير متاح، ولا يوجد إثبات runtime للجلسات الجديدة. |
| iOS | `NOT_BUILT` | لا توجد بيئة Xcode/بناء iOS في هذا السياق. |

لا توجد parity claim بين المنصات.

## 13. Tests and Validation

| البوابة | النتيجة |
|---|---:|
| Command 04 targeted backend tests | **17 passed، 1 warning**. |
| Backend non-integration suite | **2632 passed، 41 deselected**. |
| Backend integration على SQLite مهاجرة | **40 passed، 1 skipped**. |
| Frontend Vitest | **50 passed**. |
| Frontend typecheck | **ناجح**. |
| Frontend build/PWA | **ناجح**. |
| Ruff على المسارات المعدلة | **ناجح**. |
| Python compileall | **ناجح**. |
| Alembic upgrade head | **ناجح** إلى `20260815_0025`. |
| Alembic roundtrip | **ناجح**: upgrade → downgrade -1 → upgrade. |
| Alembic heads | **رأس واحد**. |
| `git diff --check` | **ناجح** قبل commit. |

تحذيرات الاختبارات الموجودة هي warnings/deprecations سابقة وليست فشل Security Gate؛ لم تُستخدم broad suppressions.

## 14. Production Verification

تمت مراجعة المصدر المحلي فقط. لم يتمكن هذا التنفيذ من إثبات:

- current main وproduction commit/runtime.
- runtime configuration الفعلية للـAsyncSession canonical.
- REDIS_URL متعدد العمال وdurable blacklist في staging.
- cookie domain/CORS/CSRF configuration في النشر الفعلي.
- feature flags الخاصة بتحويل الواجهة من legacy إلى NIAM.
- database migration state في production.
- deployment status أو cloud routing.

بناءً عليه، كل هذه البنود `UNVERIFIED`. لم يتم نشر أو تطبيق migration على production أو تغيير feature flags.

## 15. Remaining Gaps

الفجوة الأولى هي توفير `AsyncSession`/async engine رسمي لمسارات NIAM في بيئة staging، لأن المسارات canonical والخدمات typed async بينما `get_db` العام في المستودع sync. يلزم إثبات تشغيل HTTP حقيقي، transaction commit/rollback، connection pool، وfailure behavior قبل أي تفعيل.

الفجوة الثانية هي ازدواج legacy/canonical auth. يلزم عقد migration مُراجع يحدد account mapping، user-facing error states، clinical route compatibility، session cookie names، revocation semantics، وrollback plan قبل نقل LoginPage أو AuthContext.

الفجوة الثالثة هي اختبار concurrent refresh على PostgreSQL/Redis متعدد العمال، مع race-safe single-use semantics وfamily invalidation عند طلبين متزامنين. اختبارات SQLite/Mocks الحالية لا تكفي لهذا الإثبات الإنتاجي.

الفجوة الرابعة هي ربط `/security` و`/sessions` بواجهة NIAM canonical، مع account UUID مستمد server-side وعدم إعادة استخدام numeric legacy user ID. والفجوة الخامسة هي توصيل MFA/Passkey كعامل canonical primary إذا اعتمدته الجهة المالكة، دون اعتباره National Identity أو Device Biometrics.

الفجوة السادسة هي تثبيت CSRF architecture لجميع cookie-based mutations، وتغطية recovery وPasskey operations في rate-limit matrix موحدة عبر الواجهتين.

## 16. Human Approval Required

يلزم اعتماد بشري قبل أي من الإجراءات التالية: تشغيل AsyncSession provider في staging/production، تطبيق migration `0025` على قاعدة مشتركة، تحديد `NIAM_SESSION_IDLE_TIMEOUT_MINUTES` وسياسة concurrent sessions، تفعيل Redis durable، تغيير AuthContext/LoginPage من legacy إلى NIAM، ربط Passkeys/MFA primary، أو تغيير cookie/CORS/CSRF policy.

## 17. Safety Actions Not Performed

لم يتم تنفيذ production deployment أو production DB migration أو public registration activation أو government identity activation أو OCR/NFC/biometrics أو automatic merge أو push. لم يبدأ Command 05 تلقائياً.

## 18. Local Commit

سيُحفظ التنفيذ في commit محلي فقط بعد اكتمال فحص staged diff. لا توجد موافقة على push أو merge ضمن Command 04.

## References

[1]: ../../backend/app/security/auth.py "JWT creation and revocation helpers"
[2]: ../../backend/app/identity/services/authentication_service.py "Canonical NIAM authentication and session service"
[3]: ../../backend/app/identity/models/session.py "Canonical UserSession model"
[4]: ../../backend/app/identity/repositories/session_repository.py "Session and refresh-family repository"
[5]: ../../backend/app/identity/api/auth.py "NIAM authentication API"
[6]: ../../backend/app/identity/api/sessions.py "Owned session-management API"
[7]: ../../backend/app/identity/api/workspaces.py "NiamActor and server-authoritative workspace boundary"
[8]: ../../backend/app/identity/session_policy.py "Idle and absolute session policy"
[9]: ../../backend/migrations/versions/20260815_0025_authentication_session_hardening.py "Refresh-family migration"
[10]: ../../backend/tests/identity/test_authentication_command04.py "Command 04 targeted tests"
[11]: ../../frontend-v3/src/api/client.ts "Frontend transport and read/write barriers"
[12]: ../../frontend-v3/src/api/endpoints.ts "Typed legacy and NIAM auth contracts"
[13]: ../../frontend-v3/src/api/client.writeBarrier.test.ts "Frontend contract barrier tests"
