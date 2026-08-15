# GULA — P0 Identity & Account Lifecycle — Command 01

## التقرير المرجعي للحالة الفعلية

**نطاق التدقيق:** Backend و`frontend-v3` وAndroid وiOS وFlutter Desktop وCI/CD والاختبارات والإعدادات والتدقيقات.
**نوع التنفيذ:** تدقيق read-only فقط. لم يُعدّل source code أو database أو deployment أو feature flags، ولم يُنفذ merge أو migration أو DDL أو نشر.
**الفرع المفحوص:** `security/p0-bootstrap-alembic`.
**HEAD المفحوص:** `673137feb73c362c382b726b3895b0351870afaa`.
**حالة working tree عند الإغلاق:** نظيفة، بلا تغييرات غير ملتزمة.

## القرار النهائي

> **IDENTITY_LIFECYCLE_PARTIAL**

الدورة موجودة جزئياً وبها مكوّنات خلفية قوية واختبارات واسعة، لكنها ليست دورة موحدة مكتملة عبر كل المنصات، ولا يمكن اعتمادها كجاهزة للإنتاج من هذا التدقيق. السبب الرئيسي هو coexistence بين مسار NIAM canonical ومسارات `User`/`LabUser` legacy، وعدم إثبات التكامل التشغيلي الكامل بينهما في Web وAndroid وiOS وFlutter، إضافة إلى عدم إمكانية التحقق من Vercel/Railway وقاعدة الإنتاج مباشرة.

## 1. حدود السلامة والنتائج العامة

| البند | النتيجة |
|---|---|
| تعديل source | لم يحدث |
| تعديل database أو DDL أو migration | لم يحدث |
| deployment أو merge أو push | لم يحدث |
| تفعيل `PUBLIC_SELF_REGISTRATION_ENABLED` | لم يحدث؛ القيمة الافتراضية المصدرية `false` |
| تفعيل National ID/OCR/NFC/Biometrics/Passkey | لم يحدث |
| current branch | `security/p0-bootstrap-alembic` |
| current HEAD | `673137feb73c362c382b726b3895b0351870afaa` |
| working tree | نظيفة |
| remote `main` في وقت التدقيق | `1e07b8d677c5f7c94d0fb387937eff959af9589d` |
| remote `develop` في وقت التدقيق | `e4339156394f879e1eefcb027ad6eed23a95c597` |
| PRs المفتوحة | 4: #225 و#223 و#222 و#220، وكلها موجهة إلى `main` |
| Vercel/Railway live configuration | UNVERIFIED؛ لا توجد CLI محلية متاحة، ولم تُجرَ تغييرات خارجية |

## 2. نموذج الحساب والهوية

يوجد نموذج NIAM canonical مستقل يتكون من `IdentityRecord` في جدول `niam_identities`، و`Account` في `niam_accounts`، و`Membership`، و`Workspace`، و`UserSession`، إضافة إلى نماذج المؤسسات والمنشآت والأدوار والصلاحيات. يملك `Account` حالات `pending_verification` و`active` و`suspended` و`locked` و`disabled` و`deactivated`، ويحتوي على مؤشرات تحقق البريد والهاتف والهوية، وقفل المحاولات، وبيانات الجلسة الأساسية.

في الوقت نفسه ما زالت نماذج `User` و`LabUser` القديمة مستخدمة في مسارات `/login` و`/register` و`/session` وبعض عملاء الهاتف. كما يوجد `LegacyAccountLink` ومجالات توافق أخرى، لكن لم يثبت من التدقيق أن كل حساب legacy له انتقال atomically إلى Account/Identity canonical أو أن كل قرار صلاحية يمر عبر actor canonical. لذلك لا يمكن اعتبار ازدواجية النماذج مغلقة.

| Capability | Backend | Frontend | Mobile | Tests | Production | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| Person/Identity | نموذج NIAM موجود | صفحات NIAM موجودة | parity غير مثبت | اختبارات identity ناجحة | غير متحقق | PARTIAL | `backend/app/identity/models/identity.py` | ربط موحد مع legacy User/LabUser |
| Account | Account canonical + User/LabUser legacy | AuthContext يعتمد session legacy | Android/Flutter يعتمد legacy contracts | اختبارات lifecycle/auth ناجحة | غير متحقق | PARTIAL | `backend/app/identity/models/account.py`، `backend/app/models/user.py` | إزالة أو توثيق حدود legacy |
| Organization/Facility | نماذج وخدمات موجودة | guards وأدوار موجودة | سياق كامل غير مثبت | اختبارات organization/membership | غير متحقق | PARTIAL | `backend/app/identity/models` و`services` | إثبات كل سياق عبر client فعلي |
| Workspace | list/get/switch محمي بـNiamActor | routes ولوحات موجودة | memberships/permissions UX في Flutter؛ parity Android غير مثبت | اختبارات workspace ناجحة | غير متحقق | PARTIAL | `backend/app/identity/api/workspaces.py` | توحيد contract عبر المنصات |
| Role/Entitlement | خدمات authorization canonical موجودة | RoleGuard UX موجود | server decision غير مثبت من كل clients | اختبارات authorization ناجحة | غير متحقق | PARTIAL | `backend/app/identity/services/authorization_service_v2.py` | اختبار authenticated cross-platform |

## 3. Registration وOnboarding

التسجيل الذاتي العام مقفول افتراضياً في `backend/app/config.py` عبر `PUBLIC_SELF_REGISTRATION_ENABLED=false`. مسارات `/register` و`/register/citizen` و`/register/staff` و`/register/doctor` موجودة، لكنها في المسار العام تستدعي قاطعاً fail-closed عند إيقاف العلم. مسار `account-requests` يستقبل طلب مراجعة فقط، ويدعم `Idempotency-Key` وrate limit، ويصرح صراحة بأنه لا ينشئ الحساب أو يفعله مباشرة.

اختبارات التسجيل legacy تغطي duplicate prevention، التحقق من كلمة المرور، حالات inactive/pending، وإنشاء سجل التدقيق. لكن fixture الاختبار يضبط العلم إلى `True` عمداً حتى يختبر المسار؛ لذلك لا يمثل ذلك تفعيل التسجيل في الإنتاج.

| Capability | Backend | Frontend | Mobile | Tests | Production | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| Account Request | موجود review-gated ولا ينشئ حساباً مباشرة | لا توجد واجهة طلب كاملة مثبتة | غير مثبت | اختبارات account request موجودة | غير متحقق | PARTIAL | `backend/app/identity/api/account_requests.py` | إثبات مسار المراجعة والربط بالحساب |
| Public Registration | موجود لكنه fail-closed افتراضياً | `/register` صفحة إرشادية فقط | Android contract يعلن register legacy | اختبارات موجودة مع flag مفعّل داخل fixture | العلم غير مفعّل مصدرّياً | PARTIAL | `backend/app/config.py`، `frontend-v3/src/pages/auth/RegisterPage.tsx` | تنفيذ onboarding معتمد أو توثيق عدم الإتاحة |
| Duplicate Prevention | email/phone unique في النماذج ومسارات legacy؛ idempotency في account request | لا يوجد form فعلي | غير مثبت end-to-end | اختبارات legacy ناجحة | غير متحقق | PARTIAL | `register.py` و`account_requests.py` | اختبار canonical/legacy معاً |
| Approval | حالات request pending/approved/rejected/cancelled موجودة | لا توجد واجهة تشغيلية كاملة مثبتة | غير مثبت | اختبارات lifecycle جزئية | غير متحقق | PARTIAL | `account_request.py` و`account_request_service.py` | إثبات reviewer authorization والانتقال الفعلي |
| Activation | state machine canonical موجودة | لا توجد شاشة activation كاملة | غير مثبت | `test_account_lifecycle_phase1.py` ناجح | غير متحقق | PARTIAL | `account_lifecycle_service.py` | ربط approval → activation في workflow مستهلك |
| Pending/Rejected/Suspended/Deactivated | الحالات موجودة وبعض الانتقالات محكومة | route guard لا يعرض دورة الحالة كاملة | clients legacy/canonical غير موحدة | اختبارات lifecycle ناجحة | غير متحقق | PARTIAL | `AccountStatus` و`LEGAL_TRANSITIONS` | اختبار UI/client response لكل حالة |

## 4. Verification

يوجد مسار email/phone verification في `backend/app/routes/verification.py`. يستخدم رمزاً من ستة أرقام، يخزّن digest فقط، يفرض مدة 15 دقيقة وحداً أقصى للمحاولات، ويستخدم رسالة عامة لا تكشف وجود الحساب. في `ENV=demo` أو غير الإنتاج يمكن إظهار `demo_code`، أما الإنتاج فلا يعرض الرمز.

توجد مسارات إضافية للتحقق من الهوية الوطنية، OCR، biometric، WebAuthn، ومكونات ثقة وفدرالية. وجود هذه الملفات والواجهات لا يثبت أنها مفعلة في بيئة الإنتاج أو موصولة في كل عميل. لم تُفعّل أي من هذه الميزات أثناء التدقيق.

| Capability | Status | Assessment |
|---|---|---|
| Email verification | PARTIAL | Backend legacy موجود ومختبر؛ canonical Account flags موجودة؛ التكامل الموحد غير مثبت |
| Phone/OTP | PARTIAL | OTP موجود مع digest/TTL/attempt limit؛ provider delivery وend-to-end cross-platform غير مثبت |
| Identity verification | PARTIAL | مسار موجود؛ التشغيل الإنتاجي والربط canonical غير مثبت |
| Professional/Government verification | PARTIAL | نماذج وخدمات NIAM موجودة؛ workflow production غير متحقق |
| OCR | UNVERIFIED | كود document intelligence موجود، لكن لم يثبت activation أو استعماله في lifecycle |
| NFC | UNVERIFIED | لم يثبت client/production path فعال |
| Biometrics | PARTIAL | Android/iOS/Flutter biometric helpers موجودة؛ لا تُعد بديلاً عن server authentication ولا يوجد تحقق build/device هنا |
| Passkey/WebAuthn | PARTIAL | backend routes وMFAService موجودة؛ login integration وcross-platform production proof غير متحقق |

## 5. Authentication وSession

يوجد مساران للمصادقة. المسار legacy في `backend/app/routes/login.py` يبحث في `LabUser` ثم `User`، يستخدم dummy hash لمنع timing-based enumeration، ويفرض verification للمواطنين وMFA للأدوار privileged، ويضع access/refresh tokens في HttpOnly/SameSite cookies. logout يضع blacklist للـJTI ويرفع `perm_version` لإبطال الجلسات القديمة.

المسار NIAM في `backend/app/identity/api/auth.py` يستخدم `AuthenticationService` و`AccountService`. يفرض account status وis_active، يستخدم dummy hash، يقفل الحساب بعد خمس محاولات فاشلة لمدة 30 دقيقة، ينشئ access token لمدة 15 دقيقة وrefresh token لمدة سبعة أيام، ويعمل refresh rotation عبر إبطال JTI القديم وإنهاء الجلسة القديمة. `NiamActor` يتحقق من JWT account_uuid وJTI، ويربطه بحساب active وsession active.

لكن وجود المسارين يخلق قراراً غير موحد حول المصدر canonical. Android `AuthApi.kt` يستعمل `login`, `logout`, `auth/refresh`, `auth/mfa/verify`, `auth/password-reset`, `auth/me` ومسارات register legacy، بينما backend الذي فُحص يعرّف مسارات reset مختلفة (`auth/forgot-password` و`auth/reset-password`) ولا يظهر فيه contract Android مكافئ واضح لـNIAM workspace/session. Flutter يعتمد أيضاً على legacy login/session مع قراءة memberships كـUX context. هذه فجوة parity وليست فشلاً مثبتاً في كل حالة تشغيل.

| Capability | Backend | Frontend | Mobile | Tests | Production | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| Login | legacy + NIAM موجودان | `/login` متصل بالمسار العام | Android/iOS/Flutter legacy contracts | ناجح | غير متحقق | PARTIAL | `login.py`، `identity/api/auth.py`، `AuthApi.kt` | اختيار canonical واحد أو contract bridge موثق |
| Logout | blacklist + perm version في legacy؛ session terminate في NIAM | client يرسل logout ويمسح session | clients موجودة | اختبارات auth ناجحة | غير متحقق | PARTIAL | `login.py`، `authentication_service.py` | إثبات revocation الموحد لكل client |
| Refresh/Rotation | NIAM rotation؛ legacy refresh موجود | client interceptor يدعم 401/refresh | Android/Flutter/iOS refresh موجود | جزئي/ناجح حسب المسار | غير متحقق | PARTIAL | `authentication_service.py` وmobile auth managers | contract mismatch وreplay tests end-to-end |
| Expiration | JWT expiry وsession expires_at موجودان | session event/redirect موجود | validate/refresh موجود | اختبارات ذات صلة ناجحة | غير متحقق | PARTIAL | `workspaces.py`، `AuthContext`، mobile managers | اختبار deployment حقيقي |
| Revocation | DB session/JTI/blacklist/perm version موجود | frontend يتعامل مع 401 | clients تتعامل مع auth failure | ناجح في regression | غير متحقق | PARTIAL | `login.py` و`session.py` | توحيد revocation semantics |
| Device binding | UserSession.device_id موجود؛ Android sync device ID موجود | غير ظاهر كقرار auth في web | mobile binding غير مثبت في auth flow | غير مثبت end-to-end | غير متحقق | UNVERIFIED | `session.py` وmobile security | إثبات binding policy وليس مجرد field |
| MFA | TOTP وWebAuthn routes وprivileged-role gate موجودة | API methods موجودة؛ surface كامل غير مثبت | Android MFA screen موجود | اختبارات MFA جزئية | غير متحقق | PARTIAL | `mfa.py` و`mfa_service.py` | login challenge integration عبر كل platform |
| Rate limiting/lockout | rate_limit_auth + 5-attempt account lockout | status handling جزئي | client error handling موجود | tests ناجحة | غير متحقق | PARTIAL | `rate_limit.py` و`account_service.py` | Redis/shared-worker production proof |
| Recovery | `/auth/forgot-password` و`reset-password` يعملان للـUser/LabUser مع generic response | API methods موجودة ولا توجد شاشة recovery واضحة في routes | Android contract names mismatched | اختبارات auth موجودة | غير متحقق | PARTIAL | `password_reset.py` و`AuthApi.kt` | توحيد endpoints وإضافة UI/contract tests |

## 6. Authorization وContext

مسار workspace canonical يعتمد `NiamActor` الذي لا يكتفي بفك JWT؛ بل يتحقق من account status وactive session وJTI. تبديل workspace يستدعي `WorkspaceService.switch`، ويرفض الوصول ويكتب audit event عند المنع. توجد خدمات membership وorganization وauthorization وclinical gateway واختبارات cross-tenant وprivilege boundaries.

في المقابل، `frontend-v3` يحتوي RoleGuard، لكنه UX gate وليس بديلاً عن server authorization. كما أن Android وFlutter يعرضان memberships وeffective permissions كـserver-reflected UX context، لكن القرار النهائي لكل عملية سريرية أو حكومية لم يُثبت على أجهزة فعلية ضمن هذا التدقيق.

| Requirement | Status | Evidence | Gap |
|---|---|---|---|
| Server-authoritative decision | PARTIAL | `NiamActor` و`WorkspaceService` وauthorization services | عدم إثبات تغطية كل legacy route/client |
| NiamActor | COMPLETE داخل canonical workspace routes | `identity/api/workspaces.py` | لا يعني أن كل route platform يستخدمه |
| Organization/Facility/Workspace context | PARTIAL | account/membership/workspace services | cross-platform runtime proof مفقود |
| Role/Permission/Entitlement | PARTIAL | authorization services وRoleGuard واختبارات phase 7/8 | توحيد legacy role strings مع canonical permissions |
| Default deny | PARTIAL | invalid session → 401، workspace denial → 403، frontend write/read barriers | لا يعتبر كل route في المستودع مدققاً في هذا الأمر |
| Cross-tenant isolation | COMPLETE في نطاق الاختبارات التي شُغّلت | `test_tenant_isolation_matrix.py` وauthorization tests | production/database evidence غير متاح |
| Privilege escalation | PARTIAL | اختبارات authorization موجودة | لا يوجد authenticated penetration test على staging |

## 7. Audit Events والخصوصية

توجد أحداث login وlogin_failed وverification_requested وverification_failed وverification_confirmed وpassword_reset_requested وpassword_reset_completed وworkspace_switched وmembership changes وpermission decisions وحالات أمنية أخرى. سجلات legacy تستخدم identifier HMAC في failed login بدلاً من حفظ identifier raw، وتظهر مراجعة PII في sender notifications مغلقة باختبار regression.

لم يثبت أن كل انتقال canonical الخاص بـregistration وactivation وMFA/passkey changes وaccount state changes يمر دائماً عبر سجل موحد واحد. كما أن وجود audit calls في الخدمة لا يساوي تحققاً من schema/database production أو من اكتمال correlation/session metadata لكل event.

| Event | Status | Evidence | Gap |
|---|---|---|---|
| Registration/request | PARTIAL | `log_action` وAccountRequestService | توحيد canonical/legacy |
| Verification/failed verification | COMPLETE في legacy verification path | `verification.py` | canonical proofing audit غير مكتمل الإثبات |
| Activation/state changes | PARTIAL | lifecycle/audit services | تغطية كل transition وactor context |
| Login/failed login/logout | PARTIAL | legacy + NIAM services | توحيد event contract |
| Session revoke/refresh | PARTIAL | session repository/auth services | correlation موحد عبر clients |
| Recovery | PARTIAL | password reset audit calls | اختبار عدم تسجيل token/raw email في كل sink |
| MFA/passkey changes | PARTIAL | MFA routes/service | evidence production وevent completeness |
| Secrets exclusion | PARTIAL | sender privacy tests وsecurity guards | مراجعة شاملة لكل audit sink لازمة |

## 8. Frontend-v3

مسار `/register` ليس نموذج تسجيل؛ بل صفحة إرشادية تعرض أن self-service غير متاح وتعيد المستخدم إلى `/login`. مسار `/login` موجود، و`ProtectedRoute` يعيد غير المصادق إلى login، و`AuthContext`/client يتعاملان مع session و401 وsession-expired event. توجد API methods لـpassword reset وMFA وWebAuthn، لكن لا توجد في route map شاشة واضحة مكتملة لـpending/activation/recovery/security sessions تعكس دورة NIAM بكاملها.

الواجهة تحتوي صفحات NIAM governance/lifecycle/adaptive-auth، لكنها لا تثبت وحدها أن المواطن أو الموظف يمر عبر workflow lifecycle كامل، ولا تثبت أن legacy fallback غير مستخدم في كل surface. لذلك اعتُبرت frontend lifecycle **PARTIAL**.

| Surface | Status | Evidence |
|---|---|---|
| Register | PARTIAL | `RegisterPage.tsx` guidance-only، لا form فعلي |
| Login | PARTIAL | `routes/index.tsx` وLoginPage/AuthContext |
| Verify | PARTIAL | API contract موجود؛ UI lifecycle الكامل غير مثبت |
| Pending/Activation | MISSING كواجهة lifecycle مكتملة | لا route واضح في route registry |
| Recovery | PARTIAL | API methods موجودة، UI route واضح غير مثبت |
| Security/MFA/WebAuthn | PARTIAL | `mfaApi` وSecurityPage موجودان؛ end-to-end غير مثبت |
| Sessions management | MISSING كواجهة تشغيلية مكتملة | لا surface واضح لإدارة الجلسات في route map المفحوص |
| Workspace selection | COMPLETE في نطاق الواجهة canonical | workspace APIs/pages وProtectedRoute موجودة |
| 401/403/429/expired/offline/service unavailable | PARTIAL | client barriers وworkspace error mapping موجودة؛ coverage UI الشامل غير مثبت |
| Mock authentication/legacy fallback | PARTIAL | demo mode معزول ومعلن؛ legacy API paths ما زالت موجودة |

## 9. Cross-platform classification

| Platform | Registration | Login/session | Workspace/authorization | Verification/MFA | Build/test evidence | Overall |
|---|---|---|---|---|---|---|
| Web/frontend-v3 | guidance-only | implemented partially | implemented partially | API surfaces موجودة | typecheck ناجح، 49/49 frontend tests | PARTIAL |
| PWA | inherits web | inherits web | inherits web | inherits web | no separate installed PWA lifecycle proof | UNVERIFIED |
| Android | legacy register/login/refresh/MFA contracts | implemented legacy | NIAM parity غير مثبت | MFA/biometric surfaces موجودة | compile BLOCKED بسبب Android SDK | UNVERIFIED |
| iOS | AuthManager/session/biometric surfaces موجودة | legacy/refresh flow ظاهر | NIAM parity غير مثبت | biometric/MFA surfaces موجودة | xcodebuild غير متاح | UNVERIFIED |
| Flutter Desktop | AuthManager/login/refresh/memberships/biometric | implemented legacy-oriented | permissions reflected as UX context | biometric/MFA page surfaces | Flutter/Dart SDK غير متاح | UNVERIFIED |

## 10. Production readiness read-only

تم فحص references المحلية والبعيدة فقط. `origin/main` و`origin/develop` موجودان، لكن الفرع الحالي ليس production branch، وPRs مفتوحة إلى `main`. لا توجد إمكانية إثبات Vercel أو Railway live configuration من البيئة الحالية، ولا توجد CLI محلية لهما. لذلك لا يجوز تحويل إعدادات source إلى PASS production.

كما لم تُشغّل أي migration أو DDL، ولم تُتصل قاعدة production. حالة Alembic source ليست بديلاً عن التحقق من revision الفعلية في قاعدة الإنتاج، ولا يمكن اعتماد database migration state production من هذا الأمر.

| Production control | Status | Evidence | Gap |
|---|---|---|---|
| origin/main reference | UNVERIFIED | remote ref قرئ read-only | لا يعني أن production deployment على نفس commit |
| production commit | UNVERIFIED | لا وصول deployment evidence | يلزم Vercel/Railway deployment metadata |
| Vercel | UNVERIFIED | `vercel.json` فقط | يلزم dashboard/project/env/deployment evidence |
| Railway | UNVERIFIED | runbook/config فقط | يلزم environment/service/variables evidence |
| PostgreSQL migration state | UNVERIFIED | لم تُشغّل migration على production | يلزم اتصال read-only معتمد أو deployment evidence |
| Identity/Auth flags | PARTIAL | `PUBLIC_SELF_REGISTRATION_ENABLED` default false؛ flags source واضحة | runtime env الفعلي غير متحقق |
| Runtime configuration | UNVERIFIED | config guards وdocs موجودة | لا secret manager/runtime snapshot |

## 11. الاختبارات التي شُغّلت

شُغّلت الاختبارات الموجودة مسبقاً فقط، دون تعديل أو suppressions. مجموعة Backend ذات الصلة بدورة الهوية والأمان أعادت:

> **281 passed, 4 warnings in 49.17s**

وشملت lifecycle، account requests، auth/session، authorization، identity، membership، verification، workspace، rate limiting، security headers، auth infrastructure، production security config، runtime guards، registration، security regression، وtenant isolation.

شغّلت بوابات frontend-v3 الموجودة مسبقاً:

| Gate | Result |
|---|---|
| TypeScript typecheck | PASS |
| Vitest | **49/49 passed** في 14 ملفاً |
| Android `compileDebugKotlin` | BLOCKED: `SDK location not found` |
| Flutter/Dart analyze | UNVERIFIED: SDK غير متاح |
| iOS xcodebuild | UNVERIFIED: Xcode غير متاح |

التحذيرات الأربعة في Backend غير حاجبة، وتشمل deprecated `datetime.utcnow`، Starlette/httpx deprecation، تحذير JWT key size في اختبار tampering، وتحذير SQLAlchemy متعلق بدورة Foreign Keys في teardown.

نجاح الاختبارات يثبت سلوك الاختبارات المحددة فقط، ولا يثبت production readiness أو تكامل المنصات أو عزل البنية الحية.

## 12. الفجوات التي تحتاج إصلاحاً أو Security Review

### فجوات تحتاج إصلاحاً هندسياً

تحتاج المنصة إلى قرار architecture واحد يحدد NIAM canonical كمسار المصادقة والتفويض، ثم يحدد حدود legacy adapters وإيقافها تدريجياً. يجب توحيد endpoints بين Android/iOS/Flutter وbackend، خصوصاً refresh، password reset، `/session`، `/auth/me`، MFA challenge، وworkspace/membership context.

تحتاج `frontend-v3` إلى دورة lifecycle فعلية أو قرار موثق بأن onboarding يتم خارج الواجهة: request، verification، pending، approval، activation، recovery، وإدارة الجلسات. كما يجب إضافة contract evidence لكل client بدلاً من اعتبار API method أو شاشة دليل تشغيل.

### فجوات تحتاج Security Review

تحتاج مراجعة أمنية لمسار الانتقال من legacy User/LabUser إلى NIAM Account/Identity، واحتمال اختلاف قرارات الصلاحية أو session revocation بين المسارين. وتحتاج مراجعة مستقلة لاكتمال audit event coverage وعدم تسرب secrets أو raw identifiers في جميع sinks.

يحتاج WebAuthn/passkey وbiometric إلى مراجعة threat model؛ biometric المحلي ليس بديلاً عن server-side step-up. كما يجب مراجعة device binding وسياسة refresh replay في كل client.

### فجوات تحتاج Human Approval

يحتاج أي تفعيل لـ`PUBLIC_SELF_REGISTRATION_ENABLED` أو National ID/OCR/NFC/Biometrics/Passkey production approval صريحاً. وتحتاج Vercel/Railway وproduction database وsecret manager وruntime flags إلى صاحب صلاحية يثبتها من الأنظمة الحية. لا يجوز تنفيذ ذلك ضمن Command 01.

## 13. ما يجب أن تنفذه Commands 02–08

لا يبدأ هذا التقرير Command 02 تلقائياً. الترتيب المقترح هو:

| Command | نطاق العمل المقترح |
|---|---|
| Command 02 | تثبيت قرار NIAM canonical، mapping رسمي لـUser/LabUser، وcontract matrix لكل client |
| Command 03 | إغلاق التسجيل والتحقق والـapproval/activation lifecycle، مع UI أو قرار onboarding خارجي موثق |
| Command 04 | توحيد auth/session/recovery/MFA/WebAuthn وrefresh/revocation عبر Web وAndroid وiOS وFlutter |
| Command 05 | اختبار authorization وcross-tenant وprivilege boundaries على staging ببيانات synthetic وتفويض مكتوب |
| Command 06 | توحيد audit event schema، correlation، وعدم تسجيل secrets/PII، ثم Security Review |
| Command 07 | بناء بيئات staging منفصلة والتحقق من Vercel/Railway/PostgreSQL/flags/runtime |
| Command 08 | تنفيذ release-readiness gate وقرار Human Approval قبل أي production promotion |

## 14. الممنوعات التي تم احترامها

لم يتم merge أو deployment أو migration أو DDL أو production change أو feature-flag activation أو public registration activation. لم يتم تفعيل National ID أو OCR أو NFC أو biometrics أو passkey، ولم يُجرَ source refactoring لإصلاح الفجوات المكتشفة. المشاكل الأمنية وثّقت فقط ولم تُصلح في هذا الأمر، التزاماً بقاطع السلامة في Command 01.

## 15. Final Decision

# IDENTITY_LIFECYCLE_PARTIAL

**المكتمل:** نماذج NIAM الأساسية، state machine للحساب، account request review boundary، جزء معتبر من login/session/refresh/revocation، workspace actor validation، authorization services، verification legacy path، اختبارات Backend وFrontend ذات الصلة، وقفل التسجيل العام افتراضياً.

**الموجود لكنه غير مفعّل أو غير مثبت تشغيله:** public self-registration، national identity/OCR/NFC، passkey/WebAuthn end-to-end، biometric step-up، production Vercel/Railway integration، وruntime flags الحية.

**الناقص:** lifecycle UI مكتمل في frontend-v3، contract موحد لكل mobile platform، إزالة الغموض بين NIAM وlegacy، إثبات activation workflow، إدارة sessions في UI، وتحقق production/staging الحي.

**ما يحتاج إصلاحاً:** توحيد العقود والمسارات والانتقالات، ربط approval بالactivation، إكمال frontend lifecycle surfaces، ومعالجة التحذيرات non-blocking لاحقاً.

**ما يحتاج Security Review:** legacy-to-NIAM identity mapping، authorization parity، token refresh/replay، MFA/WebAuthn/biometric threat model، audit completeness، وPII/secrets sinks.

**ما يحتاج Human Approval:** أي تفعيل flags أو وصول production أو تغيير Vercel/Railway أو نشر أو migration أو تشغيل Pentest نشط.

## المراجع

[1]: ../../backend/app/identity/models/identity.py "NIAM IdentityRecord"
[2]: ../../backend/app/identity/models/account.py "NIAM Account and AccountStatus"
[3]: ../../backend/app/identity/services/account_service.py "Canonical AccountService authentication and lockout"
[4]: ../../backend/app/identity/services/account_lifecycle_service.py "Account lifecycle state machine"
[5]: ../../backend/app/identity/api/workspaces.py "NiamActor and workspace authorization context"
[6]: ../../backend/app/identity/api/account_requests.py "Review-gated account request API"
[7]: ../../backend/app/routes/register.py "Legacy registration routes and fail-closed onboarding flag"
[8]: ../../backend/app/routes/verification.py "Email/phone verification flow"
[9]: ../../backend/app/routes/login.py "Legacy login, logout, verification and privileged MFA gate"
[10]: ../../backend/app/identity/api/auth.py "NIAM login, refresh and logout API"
[11]: ../../backend/app/identity/services/authentication_service.py "NIAM session creation, rotation and termination"
[12]: ../../backend/app/routes/mfa.py "TOTP and WebAuthn routes"
[13]: ../../backend/app/routes/password_reset.py "User/LabUser password recovery"
[14]: ../../frontend-v3/src/pages/auth/RegisterPage.tsx "Frontend registration guidance-only page"
[15]: ../../frontend-v3/src/routes/index.tsx "Frontend auth/protected/workspace routes"
[16]: ../../mobile/android/app/src/main/java/io/gula/android/data/remote/api/AuthApi.kt "Android legacy auth contract"
[17]: ../../mobile/desktop/lib/core/auth/auth_manager.dart "Flutter auth manager and membership context"
[18]: ../../backend/app/config.py "PUBLIC_SELF_REGISTRATION_ENABLED and runtime flags"
[19]: ../../docs/STAGING_RUNBOOK.md "Staging isolation and promotion boundary"
