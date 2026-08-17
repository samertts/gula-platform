# GULA Platform — Command 04

## Authentication + Session Hardening Report

**المنصة:** GULA Platform
**الفرع:** `chore/security-ddos-hardening-clean`
**Pull Request:** [#226](https://github.com/samertts/gula-platform/pull/226)
**التاريخ:** 2026-08-16
**المؤلف:** **Manus AI**
**قرار Command 04:** **`SECURITY_BLOCKED — AUTHENTICATION_PARTIAL`**
**الحكم الأمني:** تم إصلاح دورة المصادقة والجلسة والتدوير والإبطال على مستوى الخادم، وأصبحت مسارات replay وCSRF وMFA وworkspace context وrate limiting fail-closed في الحدود التي يمكن إثباتها محلياً. أثناء التدقيق اكتُشف keystore إنتاجي وملف signing properties متتبعان في Git؛ لذلك فُعّل **SAFE_STOP**، وأزيلت الأسرار من working tree وأضيفت حواجز جديدة، لكن لا يمكن رفع الحظر قبل تدوير/إبطال المفتاح وكلمات المرور خارجياً ومعالجة التاريخ وفق إجراء أمني معتمد. كما تبقى أدلة Android/iOS/Flutter وPostgreSQL/Redis وVercel الخارجية غير مكتملة.

## 1. الملخص التنفيذي

استهدف Command 04 دورة المصادقة الكاملة: **Login → Authentication → Session → Refresh → Workspace Context → Logout → Revocation**. شملت المراجعة المسارات legacy وNIAM، cookies وbearer tokens، session idle/absolute expiry، refresh rotation وreplay، logout، account namespace isolation، CSRF، global وroute-level rate limits، MFA/TOTP/WebAuthn، audit، وواجهات Web/PWA/Android/iOS/Flutter Desktop.

أُغلقت فجوات أمنية مؤثرة. أصبح فشل login يحفظ lockout قبل إعادة `401`، وأصبحت عمليات terminate للجلسات تحفظ transaction، وأصبح idle timeout مفروضاً على actor الخاص بـNIAM مع sliding touch مضبوط. كما أصبح refresh token single-use ذرياً، ويؤدي replay إلى إبطال عائلة الجلسات كاملة عبر زيادة `perm_version` بدلاً من رفض token واحد فقط. وأصبحت تحديات WebAuthn single-use عبر `get_and_delete`، وتحقق MFA session ذرياً بشرط compare-and-swap، وجميع عمليات MFA الحساسة محمية بمحددات معدل.

تم تثبيت الفصل بين عقود الويب والتطبيقات الأصلية. الويب لا يعيد bearer material في JSON ويستخدم HttpOnly cookies، بينما لا يرسل الخادم token JSON إلا عندما يعلن العميل native platform صراحةً عبر `X-Client-Platform`. كما تم ربط iOS بـserver-authoritative `/logout` قبل تنظيف الحالة المحلية، وحفظ rotated refresh token في iOS وAndroid. لا توجد قاعدة بيانات إنتاجية أو متغيرات بيئية أو إعدادات Vercel عُدلت أثناء هذا الأمر.

> النتيجة العملية: **Backend authentication/session hardening مثبت بالاختبارات المحلية، لكن الحالة الكلية تبقى `AUTHENTICATION_PARTIAL` بسبب حدود toolchain وstaging وVercel protection، لا بسبب bypass مثبت في الخادم.**

## 2. نطاق المراجعة وقواعد القرار

اعتمدت المراجعة مبدأ أن **الخادم هو مصدر الحقيقة الوحيد** للصلاحيات، verification state، session state، وworkspace context. لا يُعامل `assurance_level` وحده كصلاحية، ولا يسمح العميل بترقية verification أو membership أو workspace أو session state. كما بقيت Contact Verification منفصلة عن Identity وProfessional وOrganization وGovernment Verification، وبقيت المزودات غير المتصلة fail-closed دون OCR أو NFC أو Biometrics أو Government Identity وهمي.

| قاعدة أمنية | طريقة التحقق في Command 04 | الحكم |
|---|---|---|
| Server-authoritative authorization | actor dependencies وworkspace switch وmembership/role routes تقرأ القرار من الخادم | **PASS محلياً** |
| No public registration | `PUBLIC_SELF_REGISTRATION_ENABLED=false` افتراضياً، وAccount Request هو المسار المعتمد | **PASS في default config** |
| No client-controlled session/workspace | session وworkspace context يعادان من API، وswitch يتم عبر endpoint خادمي | **PASS محلياً** |
| No token/password/OTP/session secret logging | grep محدد على ملفات auth المعدلة، وaudit details لا تحتوي token material | **PASS ضمن الملفات المعدلة** |
| Provider failure لا يصبح success | MFA challenge store وRedis production guard يعيدان `503` عند غياب shared backend | **PASS محلياً** |
| SAFE_STOP conditions | لا توجد نتيجة اختبار تشير إلى bypass أو cross-tenant access؛ toolchain/staging gaps بقيت معلنة | **لا SAFE_STOP code finding؛ ما زالت جاهزية الإنتاج جزئية** |

## 3. Findings والإصلاحات

| Finding | المشكلة والسبب الجذري | الإصلاح المنفذ | Security Evidence والاختبارات | المخاطر المتبقية |
|---|---|---|---|---|
| **F-01 — Login failure commit** | كان lockout state يُحدّث ثم تُعاد `401` قبل حفظ transaction، فكان الفشل لا يثبت دائماً. | أضيف commit قبل إعادة نتيجة login الفاشلة في NIAM auth. | `tests/identity/test_auth_api_security.py` وfull backend suite. | سلوك PostgreSQL تحت transaction isolation لم يُجرّب على staging. |
| **F-02 — Session terminate commit** | terminate وterminate-all كانا ينجزان ownership check دون `await db.commit()`، فكان الإبطال قد يتحول إلى no-op. | أضيف commit بعد التحقق من الملكية والتنفيذ في NIAM session API. | اختبارات session security وfull suite. | لا يوجد replay مثبت؛ rehearsal الخارجي غير منفذ. |
| **F-03 — Idle timeout وsliding touch** | actor الخاص بـNIAM لم يفرض inactivity expiry، وكانت الجلسة قد تبقى صالحة بعد الخمول. | أضيفت `SESSION_IDLE_TIMEOUT_MINUTES` بحدود 5–1440، و`SESSION_TOUCH_INTERVAL_SECONDS` بحدود 10–3600، مع helpers sync/async وتطبيقها على dependencies. | `test_workspace_api_hardening_phase5.py`: idle expiry وtouch throttling، ضمن 2704 tests. | يلزم قياس clock/DB behavior في PostgreSQL production-like. |
| **F-04 — Rejected account lifecycle** | لم يكن `rejected` status جزءاً من state machine، وكان deny-by-default غير مكتمل. | أضيف `AccountStatus.rejected`، وانتقال `pending_verification → rejected`، وحالة نهائية بلا reactivation، مع رفض authenticate timing-safe. | `test_foundation_phase0_phase1.py` واختبارات lifecycle الكاملة. | قرار إعادة النظر في rejected يجب أن يبقى governance/manual، وليس reactivation API. |
| **F-05 — Refresh rotation وfamily replay** | replay كان يرفض token المعاد استخدامه فقط، فلا تُبطل بقية عائلة الجلسات. | أضيف atomic `consume_refresh_jti`، وblacklist كطبقة ثانية، و`_revoke_after_refresh_replay()` الذي يزيد `perm_version` ويلغي كل الجلسات عند blacklist hit أو atomic consume failure. | `test_refresh_rotation_security.py` يثبت single-winner، expiry، shared-cache guard، وfamily revocation audit؛ full suite ناجح. | يلزم اختبار multi-worker حقيقي خلف Redis production وPostgreSQL. |
| **F-06 — WebAuthn challenge reuse** | challenge كان قابلاً لإعادة القراءة، كما أن credential ID غير المعروف لم يكن يستهلك challenge في كل المسارات. | أضيف `get_and_delete` ذري في memory/Redis، وأصبح authentication يستهلك challenge قبل device lookup. | `test_mfa_security.py` يثبت single-use حتى مع unknown credential، مع fail-closed cache test. | WebAuthn cryptographic verification نفسها تحتاج iOS/Android hardware CI؛ لا توجد passkey login claim جديدة. |
| **F-07 — MFA session race** | concurrent verification كان يمكن أن ينجح مرتين قبل تثبيت `is_verified`. | أضيف compare-and-swap update بشرط `is_verified=false` وexpiry، ولا يُقبل إلا `rowcount == 1`. TOTP devices تستخدم `with_for_update()`. | `mfa_service.py` وfull suite وMFA targeted tests. | يلزم إثبات row-lock behavior على PostgreSQL، لأن معظم الاختبارات المحلية SQLite. |
| **F-08 — MFA abuse controls وprovider failure** | بعض TOTP/WebAuthn/device routes لم تكن تمر عبر rate limiter، وفشل challenge cache كان يمكن أن يتحول إلى 500 عام. | أضيف `_rate_limit_mfa()` لكل setup/verify/begin/complete/list/remove/status، وأصبحت unavailable challenge stores تعيد `503` دون نجاح. | `mfa.py` route review، `test_mfa_security.py`، full suite. | حدود المعدل تحتاج calibration ميداني بعد مراقبة false positives. |
| **F-09 — Native token contract** | login كان يعيد token JSON لعقود عامة، بما يزيد خطر وصول bearer material إلى JavaScript أو logs. | web يبقى cookie-only، وnative token JSON يتطلب `X-Client-Platform` المقبول؛ أضيف header للـAndroid وFlutter Desktop، وiOS يرسله ضمن session defaults. | `test_security_demo_contract.py` يثبت web no-token وnative token contract. | native CI غير كامل؛ header لا يمنح authorization بحد ذاته، لكن يجب إبقاء allowlist server-side. |
| **F-10 — Rotated refresh token persistence** | iOS وAndroid كانا يحفظان access token الجديد دون refresh token الدوار، ما قد يعيد استخدام family قديم. | iOS يحفظ `refresh_token` الجديد في Keychain، وAndroid يحفظه في EncryptedPrefs في interceptor وAuthenticator. | code evidence في `APIClient.swift` و`AuthInterceptor.kt`؛ Android source compile محجوب بسبب SDK. | Android SDK وiOS/Xcode CI مطلوبان لإثبات compile/runtime. |
| **F-11 — iOS logout local-only** | `AuthManager.logout()` كان ينظف local state فقط ولا يستدعي revocation الخادمي. | أضيف `APIEndpoint.logout`، و`APIClient.serverLogout(accessToken:)` دون refresh/retry، وأصبح `logout()` و`forceLogout()` ينتظران server revoke ثم ينفذان local cleanup كـfallback عند فشل الشبكة. | `AuthManager.swift`, `APIClient.swift`, `AuthManagerTests.swift`; Xcode غير متوفر محلياً. | iOS status **UNVERIFIED** إلى أن يمر Xcode/Simulator/device CI. |
| **F-12 — CSRF registration وrefresh cookie** | كان يلزم إثبات أن `CSRFMiddleware` مسجل فعلياً، كما كان `/auth/refresh` يتجاوز guard إذا غاب access cookie مع بقاء refresh cookie. | factory يسجل `CSRFMiddleware` و`GlobalRateLimitMiddleware`، وCSRF يفحص access أو refresh cookie، ويرفض browser mutation بلا Origin/Referer أو من origin غير مسموح. | middleware registration test وcross-origin logout/refresh tests؛ 16 contract tests ناجحة. | CORS/proxy origin configuration يجب التحقق منه في production edge الحقيقي. |
| **F-13 — Global rate-limit registration/failure mode** | وجود helper وحده لا يكفي؛ كما أن in-memory fallback في production قد يسمح بتجاوز الحد بين workers. | middleware مسجل فعلياً، والـhealth paths فقط exempt، وproduction يعيد `503` عند غياب shared Redis أو فشل backend بدلاً من fail-open. | registration test وfail-closed test؛ targeted Ruff وfull suite. | يلزم Redis outage drill متعدد workers وقياس limits عبر gateway/WAF. |
| **F-14 — Audit action consistency** | login failures/success/logout كانت تستخدم أسماء متفرقة، ما يضعف detection والـSIEM correlation. | توحيد الفشل إلى `login_failure` والنجاح إلى `login_success` والخروج إلى `logout`، مع `refresh_replay_detected` و`token_refresh` دون أسرار. | grep على ملفات auth المعدلة، audit assertions، وfull suite. | يلزم mapping نهائي مع SIEM schema وretention policy خارج هذا الأمر. |

## 4. Authorization وWorkspace Context

يُستخرج actor من server-side session/JWT بعد التحقق من `account_kind`، ولا يسمح token legacy غير محدد النطاق بالوصول إلى `LabUser` أو `User` بالحدس. هذا يعالج numeric ID namespace collision بين مواطن وحساب مؤسسة. عمليات workspace list وswitch وmembership وeffective permissions تبقى server-authoritative، وتعيد context version وworkspace summary من الخادم؛ الواجهة لا تنشئ context محلياً ولا تعتبر selection نجاحاً قبل response خادمي.

| السطح | السلوك الذي تم إثباته | الدليل |
|---|---|---|
| NIAM actor | idle timeout وabsolute expiry وthrottled touch | `workspaces.py` وworkspace hardening tests |
| Workspace switch | endpoint خادمي، conflict recovery، rollback إلى workspace السابق عند الفشل | `WorkspaceSelector.tsx` و`WorkspaceSelector.test.tsx` |
| Membership/roles | قراءات memberships/effective permissions من الخادم، وwrites محكومة بعقود واضحة | `AuthContext.tsx` وAPI client write barrier |
| Frontend navigation | permission-filtered navigation لا يمنح permission؛ القرار يبقى backend | `Sidebar.tsx` وpermission tests |
| Expired session | single-flight refresh، ثم event `gula:session-expired` ومسح identity وطلب re-auth | `client.ts`, `AuthContext.tsx`, `authState.ts` |

## 5. Cross-platform parity matrix

لا تعني كلمة **PASS** هنا أن كل native SDK بُني محلياً؛ بل تعني أن contract source وtests المتاحة أثبتت السلوك المحدد. حيث تعذر toolchain، تم استخدام **UNVERIFIED** أو **PARTIAL** عمداً بدلاً من ادعاء parity غير مثبتة.

| المنصة | Login contract | Session/refresh | Logout/revocation | Workspace/UX | CI evidence | القرار |
|---|---|---|---|---|---|---|
| Web | cookie-only JSON؛ لا access/refresh/token في body | HttpOnly cookies، single-flight refresh، 401 → re-auth | `/logout` server-authoritative مع cookie | workspace selection من server context؛ session-expired banner/login | 61 unit، 53 E2E، typecheck/lint/build | **PASS محلياً** |
| PWA | نفس Web contract؛ لا bearer في JavaScript | نفس cookie/session path؛ service worker محجوب في deterministic E2E | نفس `/logout` | نفس workspace/auth UX، responsive E2E | PWA build ناجح و53 E2E | **PASS للـweb/PWA build؛ device install غير منفذ** |
| Android | `X-Client-Platform: android` يعطي token JSON للعقد native فقط | AuthInterceptor وTokenAuthenticator يحفظان rotated refresh token | server route متاح عبر native auth header | API contract موجود؛ native workspace runtime غير مشغّل | Gradle wrapper موجود، لكن compile فشل قبل source بسبب Android SDK غير موجود | **PARTIAL / UNVERIFIED** |
| iOS | `X-Client-Platform: ios` ضمن session headers | rotated refresh token محفوظ في Keychain | `/logout` يُستدعى قبل local cleanup، وforceLogout كذلك | API contract موجود؛ SwiftUI runtime غير مشغّل | `xcodebuild` و`swiftc` غير متوفرين | **PARTIAL / UNVERIFIED** |
| Flutter Desktop | `X-Client-Platform: desktop` ضمن API client | refresh/logout endpoints موجودة في API layer بحسب source inventory | server-authoritative endpoint موجود في client contract | workspace APIs موجودة؛ desktop runtime غير مشغّل | Flutter/Dart غير متوفران | **UNVERIFIED** |

## 6. الاختبارات والأدلة

| الاختبار أو الفحص | النتيجة |
|---|---:|
| Backend full suite | **2704 passed, 4 skipped** خلال **297.31 ثانية** |
| Backend targeted Command 04 suite قبل الإضافات النهائية | **71 passed** |
| Refresh/MFA/CSRF contracts بعد التعديلات | **4 + 2 + 16 tests passed** ضمن full suite؛ regression tests كلها ناجحة |
| Frontend TypeScript | **PASS** |
| Frontend ESLint | **PASS** |
| Frontend unit tests | **61 passed / 17 test files** |
| Frontend production build | **PASS** |
| Frontend Playwright E2E | **53/53 passed** |
| Android `:app:compileDebugKotlin` | **BLOCKED قبل compile**: Android SDK location غير موجود |
| iOS Xcode/Swift compile | **UNVERIFIED**: `xcodebuild` و`swiftc` غير متوفرين |
| Flutter/Dart checks | **UNVERIFIED**: Flutter وDart غير متوفرين |
| Ruff على كل backend app/tests بـ`E9,F,I001` | **169 مخالفة I001** في ملفات موجودة خارج نطاق Command 04؛ لم تُعدّل لتجنب scope creep |
| Ruff على ملفات Command 04 المعدلة | **PASS — All checks passed** |
| Bandit على auth/MFA/Redis routes | **PASS — لا findings عند `-ll`** |
| `git diff --check` | **PASS** |

رسائل `ECONNREFUSED` التي ظهرت في log خادم Vite أثناء E2E تخص API المحلي غير المشغّل؛ لم تفشل أي حالة Playwright، لأن الاختبارات تستخدم عقود mocking/bridge المقصودة. لم تُخفَ هذه الملاحظة ولم تُعتبر دليلاً على صحة backend runtime.

توجد warnings عامة في backend، منها deprecated `datetime.utcnow()` وStarlette/httpx وSQLite foreign-key drop ordering. لم تسبب فشلاً، لكنها ليست جزءاً من قرار authentication hardening، ولذلك لم تُحوّل إلى refactor واسع.

## 7. Production Safety Gate — read-only

| الفحص | النتيجة | الملاحظة |
|---|---|---|
| `PUBLIC_SELF_REGISTRATION_ENABLED` | **SAFE DEFAULT: false** | التسجيل العام مغلق؛ Account Request فقط حسب policy. |
| `ENABLE_API_DOCS` | **SAFE DEFAULT: false** | factory لا يفتح docs في production إلا بتفعيل صريح. |
| Production Redis/rate limit | **FAIL-CLOSED في code** | middleware وMFA/refresh guards تعيد `503` عند غياب shared backend. قيمة production الفعلية لم تُعدّل. |
| Alembic heads | **PASS: single head `20260815_0022`** | `alembic heads` نجح؛ لا migration جديدة تخص Command 04. |
| PostgreSQL/Alembic rehearsal | **UNVERIFIED** | الاختبارات المحلية SQLite؛ لا PostgreSQL staging متاح. |
| Git/PR | **PASS read-only** | branch صحيح، local/remote HEAD قبل commit كان `2f55295c`، وPR #226 مفتوح على `main`. |
| Vercel project | **READ-ONLY OBSERVED** | project `gula-platform`، framework `vite`، latest deployment `dpl_6PRqvCTT85xLdrrbRR7Z2CeiXcwM` وحالته `BLOCKED`، و`live=false`. |
| Vercel protection | **EXTERNAL BLOCKER** | SSO protection مفعلة على `all_except_custom_domains`؛ password protection وtrusted IPs معطلتان. لم يتم تعديل أي setting. |
| Production DB/env/deployment mutation | **PASS: none performed** | لم تُشغّل migrations على production، ولم تُغيّر env أو Vercel أو deployment. |

## 8. حدود ومخاطر متبقية

أهم حد متبقٍ هو عدم توفر بيئة PostgreSQL staging أو production-like. SQLite أثبت contract logic، لكنه لا يثبت وحده سلوك row locks وtransaction isolation وRedis multi-worker atomicity. قبل إطلاق authentication hardening على نطاق واسع، يجب تنفيذ rehearsal على PostgreSQL وRedis مشتركين، مع اختبار concurrent refresh، terminate-all، TOTP/WebAuthn verification، وworkspace switch تحت أكثر من worker.

Native parity ما زالت جزئية من ناحية الإثبات التنفيذي. Android compile توقف بسبب SDK directory غير موجود، وFlutter/Dart وXcode غير متاحة في sandbox. لذلك لا ينبغي دمج هذه النتيجة مع claim بأن binaries mobile/desktop جاهزة. التغييرات المصدرية موجودة ومراجعة، لكنها تحتاج CI فعلياً.

Vercel `BLOCKED` ليس فشلاً في هذا الكود وفق القراءة الحالية؛ effective protection أظهر SSO enabled خارج custom domains. لا يجوز تعطيل SSO أو trusted controls تلقائياً لمعالجة الحظر. يلزم owner/account action في Vercel أو مراجعة collaboration/protection policy، ثم إعادة قراءة deployment read-only بعد إنشاء deployment جديد.

الـwhole-repository Ruff gate ما زال يعرض 169 مخالفة I001 سابقة في ملفات متعددة. تم إبقاء scope منضبطاً: ملفات Command 04 المعدلة تمر `E9,F,I001`، لكن repository-wide import formatting ليس أخضر بعد، ولا ينبغي وصفه بأنه clean بالكامل.

## 9. القرار النهائي

قرار Command 04 هو **`SECURITY_BLOCKED — AUTHENTICATION_PARTIAL`**. لا يوجد authentication bypass مثبت في الاختبارات، لكن اكتشاف signing material إنتاجي متتبع في Git هو blocker أمني مستقل يتطلب تدويراً/إبطالاً خارجياً ومراجعة تاريخ المستودع. إضافة إلى ذلك، يتطلب إثبات الجاهزية الكاملة **PostgreSQL/Redis staging rehearsal، Android/iOS/Flutter native CI، وإزالة أو تفسير Vercel deployment block خارج الكود**.

داخل نطاق backend والواجهة المتاحة، تم تنفيذ hardening جوهري ومثبت: server-authoritative session lifecycle، idle/absolute expiry، atomic refresh rotation، family-wide replay revocation، cookie-only Web contract، native token boundary، server-authoritative logout، CSRF middleware registered and refresh-cookie protected، global rate-limit middleware registered and fail-closed، MFA/WebAuthn single-use، audit normalization، وworkspace context isolation. لا يجوز تفعيل مزودات Government/Professional/Organization أو أي biometric/OCR/NFC path اعتماداً على هذا الأمر؛ تبقى تلك المسارات **PROVIDER_DEPENDENCY** وفق قرار Command 03.

الإجراء الآمن التالي هو دفع commit إلى PR #226، تشغيل CI native وPostgreSQL على بيئة مخصصة، ثم إعادة فحص Vercel deployment protection read-only. إذا نجحت تلك الأدلة ولم يظهر drift أو isolation regression، يمكن إعادة تقييم الحالة من `AUTHENTICATION_PARTIAL` إلى قرار جاهزية أقوى.

## 10. المراجع الداخلية

[1]: ../backend/app/routes/login.py "Legacy login/logout and web/native response contract"
[2]: ../backend/app/routes/mobile.py "Refresh rotation, replay family revocation, and native refresh contract"
[3]: ../backend/app/security/auth.py "JWT account scope and atomic refresh JTI consumption"
[4]: ../backend/app/security/redis_client.py "Atomic cache primitives and shared-backend marker"
[5]: ../backend/app/security/csrf.py "Registered CSRF double-submit/origin guard"
[6]: ../backend/app/middleware.py "Global rate-limit and fail-closed traffic protection middleware"
[7]: ../backend/app/security/mfa_service.py "TOTP, WebAuthn single-use challenge, and MFA CAS verification"
[8]: ../backend/app/identity/api/workspaces.py "NIAM idle timeout and sliding touch"
[9]: ../backend/app/identity/api/sessions.py "Server-authoritative session termination"
[10]: ../backend/app/identity/services/account_lifecycle_service.py "Rejected terminal lifecycle state"
[11]: ../backend/tests/identity/test_refresh_rotation_security.py "Refresh replay and shared-cache regression tests"
[12]: ../backend/tests/identity/test_mfa_security.py "MFA challenge and fail-closed cache tests"
[13]: ../backend/tests/test_security_demo_contract.py "Web/native token boundary, CSRF, middleware registration, and safety contracts"
[14]: ../frontend-v3/src/api/client.ts "Frontend refresh single-flight and session-expired event"
[15]: ../frontend-v3/src/contexts/AuthContext.tsx "Frontend identity/session/workspace lifecycle"
[16]: ../frontend-v3/src/components/workspace/WorkspaceSelector.tsx "Server-authoritative workspace UX and conflict recovery"
[17]: ../mobile/ios/Gula/Core/Auth/AuthManager.swift "iOS server-authoritative logout and local fallback"
[18]: ../mobile/ios/Gula/Core/Networking/APIClient.swift "iOS refresh persistence and direct logout request"
[19]: ../mobile/android/app/src/main/java/io/gula/android/data/remote/interceptor/AuthInterceptor.kt "Android rotated refresh persistence"
[20]: ../mobile/desktop/lib/core/api/api_client.dart "Flutter Desktop platform contract"
[21]: ../backend/app/config.py "Safe production defaults and session timeout bounds"
[22]: https://github.com/samertts/gula-platform/pull/226 "Command 04 pull request"

**التوقيع:** Manus AI
**الحالة:** هذا التقرير محدث بعد SAFE_STOP وreassessment المحلي؛ سيُثبت مع الإصلاحات الحالية في PR #226. لا يوجد force-push أو history rewrite.

## 11. SAFE_STOP Addendum — Android Signing Material

في 2026-08-17 اكتشف التدقيق أن المستودع كان يتتبع `mobile/android/app/keystore/gula-production.jks` و`mobile/android/app/signing.properties`. الملف الأول binary keystore بحجم 2796 بايت، والملف الثاني يحتوي مفاتيح إعداد signing مثل `storePassword` و`keyPassword`. لم تُطبع أي قيمة سرية أو private key، ولم يُجرَ أي تدوير أو إبطال خارجي تلقائياً.

| الإجراء | النتيجة الحالية | الدليل المحلي |
|---|---|---|
| إزالة keystore وsigning properties من working tree | **PASS** | لا توجد ملفات `.jks` أو `signing.properties` حالياً تحت `mobile/android` |
| منع عودة الملفات | **PASS** | `.gitignore` يمنعها، مع السماح فقط بـ`signing.properties.example` |
| CI-only signing | **PASS محلياً** | Gradle يقرأ `android.injected.signing.*` فقط؛ release بلا properties يفشل برسالة fail-closed |
| CI material handling | **PASS source review** | `umask 077`، `printf`، `chmod 600`، وcleanup للـkeystore/service account بعد الاستخدام |
| Secret guard | **PASS** | `check_public_secrets.py` يرفض tracked `.jks` و`signing.properties` ويعيد `OK` بعد staging |
| Gradle help | **PASS** | `:app:help` نجح |
| Debug Android build | **ENVIRONMENT BLOCKED** | فشل قبل compile لأن Java toolchain المتاحة لا توفر `JAVA_COMPILER` |
| Release بدون أسرار | **PASS fail-closed** | `bundleRelease` رفض التنفيذ برسالة `Release signing is not configured` |
| External key rotation/revocation | **REQUIRED / UNVERIFIED** | لم يتم الوصول إلى Google Play/App Signing أو CI secret manager |
| Git history purge | **REQUIRED / NOT PERFORMED** | لا force-push ولا history rewrite؛ يلزم إجراء بشري معتمد |

بسبب بقاء المفتاح الإنتاجي وكلمات المرور محتملة التعرض في تاريخ Git، لا يجوز تصنيف Command 04 كـPASS بعد إزالة الملفات الحالية فقط. يلزم أولاً إبطال/تدوير Android production signing key و`storePassword` و`keyPassword` في الجهة المالكة، تدوير أي CI secrets مرتبطة به، ثم تنفيذ إجراء معتمد لتنظيف التاريخ أو احتواء أثره دون تجاوز سياسة منع force-push. إلى أن تثبت هذه الخطوات، يبقى **P4 `SECURITY_BLOCKED`** وP5 وCommand 05 محجوبين.

## 12. Final Security Regression After SAFE_STOP Remediation

| Evidence | Result |
|---|---:|
| Command 04 adversarial/security suite | **437 passed, 3 skipped, 3 warnings** |
| BOLA/tenant isolation proof subset | **83 passed, 2 warnings** |
| Person/device route actor-gating regression | **69 passed, 1 warning** |
| OpenAPI route tracer | **PASS** |
| Frontend dependency audit | **0 vulnerabilities across 190 production/optional dependencies** |
| YAML/template validation | **PASS** |
| Staged `git diff --check` | **PASS** |
| Production/DB/deployment mutation | **NONE** |

The security suite covers authentication, refresh replay, session scope, MFA, recovery, verification, membership, workspace, audit integrity, CSRF, rate limiting, runtime isolation, production configuration, headers, clinical authorization, LIMS/radiology tenant isolation, and token forgery. These results establish local regression safety; they do not substitute for external key rotation, Git-history containment, native release builds, PostgreSQL/Redis rehearsal, or production deployment evidence.

## 13. Blocker Reassessment — 2026-08-17

أُعيدت مراجعة أسباب الحظر بعد طلب الاستمرار. أُصلحت regressions داخلية قابلة للإصلاح في ملفات الاختبارات فقط: أضيفت annotations المطلوبة لاختبار cross-account device fingerprint والدالة المحلية التي تفحص routes، وأزيلت imports المكررة وI001/F811 من `test_niam.py`. لم يتغير authorization behavior أو production configuration بسبب هذه الإصلاحات.

| الفحص المحلي بعد الإصلاح | النتيجة |
|---|---:|
| Full backend regression | **2723 passed, 4 skipped, 172 warnings** خلال **317.53 ثانية** |
| Targeted NIAM/security review tests | **50 passed, 1 warning** |
| Changed-files Ruff/MyPy quality gate | **PASS**؛ لا توجد MyPy regressions جديدة |
| Ruff على الاختبارين المعدلين | **PASS** |
| Frontend lint/typecheck/build | **PASS** |
| Frontend unit tests | **68 passed / 19 files** |
| Workflow/compose YAML validation | **PASS** |
| Secret guard | **PASS** |
| Python syntax/compile gates | **PASS** |
| `git diff --check` | **PASS** |

ظل constitution diagnostic المحلي يعرض Rule 5 وRule 10 وRule 15 كفشل واسع النطاق: **421 duplicate blocks** وlegacy flake8/pyflakes findings و**1998 potentially unused symbols** عبر 123 ملف Python. هذه النتائج ليست regression ناتجة عن إصلاحات IAM الأخيرة، ولا يجوز حلها بإيقاف القاعدة أو `noqa` واسع أو حذف آمن غير مثبت؛ لذلك بقيت موثقة كـlegacy debt خارج scope Command 04 بدلاً من تزوير PASS. كما أن workflow نفسه لا يجعل نتيجة enforcer blocking، إذ ينفذ الأمر مع `|| echo "FAILED"`، بينما فشل GitHub المرصود حدث قبل أي step.

### CI runner evidence

تم فحص jobs الخاصة بالـSHA `79113e58d7ba8c8cf830486db88c9d9c954f25b0` عبر GitHub Actions metadata. jobs الفاشلة في IAM Hardening وQuality Gate وFrontend/PWA وAndroid/iOS/Flutter وCodeQL وSecurity Hardening وغيرها كانت جميعها `runner_id=0` و`steps=[]`، مع إكمال الفشل خلال ثوانٍ وعدم وجود failed logs. هذا يثبت **pre-execution runner/infrastructure blocker** وليس failure في source step يمكن إصلاحه من داخل المستودع [23] [24] [25] [26]. لا يجوز تحويل هذه النتيجة إلى PASS حتى يعمل runner فعلياً ويصدر logs وartifacts.

| سبب الحظر | ما أمكن إصلاحه محلياً | الحالة الحالية |
|---|---|---|
| Changed-files MyPy regression | تم إصلاح annotations والتحقق بالـquality gate | **CLOSED LOCALLY** |
| Targeted import/functional lint | تم إصلاح I001/F811 في الملف المعدل | **CLOSED LOCALLY** |
| GitHub Actions jobs بلا runner | لا يوجد تغيير مصدر يعالج runner allocation أو GitHub infrastructure | **BLOCKED_EXTERNAL** |
| Android signing key/password exposure | أزيلت الملفات، وأصبح signing CI-only وfail-closed | **EXTERNAL ROTATION REQUIRED** |
| Git history containment | لم ينفذ بسبب منع force-push وغياب governance authorization | **GOVERNANCE BLOCKED** |
| Vercel/SSO and native toolchains | لا صلاحية/بيئة كافية لإثباتها من sandbox | **UNVERIFIED** |

لا يمكن إلغاء الحظر الأمني أو الادعاء بتحقق كافة الشروط قبل تنفيذ **تدوير/إبطال Android production signing key، تدوير CI secrets، وhistory containment المعتمد**. وبالمثل، لا يمكن إلغاء حظر CI من داخل الكود ما دام GitHub لا يخصص runner. لذلك يبقى قرار Command 04 **`SECURITY_BLOCKED — AUTHENTICATION_PARTIAL`**، ويبقى P5 **`P5_BLOCKED_BY_PREREQUISITE`**.

[23]: https://github.com/samertts/gula-platform/actions/runs/32056253766 "IAM Hardening Gate — runner pre-execution failure"
[24]: https://github.com/samertts/gula-platform/actions/runs/32056253725 "Quality Gate — runner pre-execution failure"
[25]: https://github.com/samertts/gula-platform/actions/runs/32056253729 "Android CI/CD — runner pre-execution failure"
[26]: https://github.com/samertts/gula-platform/actions/runs/32056253730 "Security Hardening — runner pre-execution failure"

## 14. CI Rerun Evidence After Internal Fixes

بعد دفع commit `33664e8df0aee1dc43528abbd09d14b5d8d8c95b`، أُعيد تشغيل jobs الفاشلة فقط في جميع workflows ذات الصلة، ثم فُحصت المحاولة الثانية `run_attempt=2`. النتيجة لم تتغير: كل job انتهى خلال 2–6 ثوانٍ تقريباً بحالة `failure` و`runner_id=0` و`steps=[]`. أما jobs التابعة لها التي تعتمد على تلك النتائج فكانت `skipped`؛ ولا يجوز اعتبار skipped دليلاً على PASS.

| workflow | current run | attempt-2 job evidence | النتيجة |
|---|---|---|---|
| IAM Hardening Gate | [32060318297][27] | job `95480208126` | failure قبل التنفيذ؛ runner_id=0؛ steps=0 |
| Changed Files Quality Gate | [32060318338][28] | job `95480211103` | failure قبل التنفيذ؛ runner_id=0؛ steps=0 |
| Security Hardening | [32060318515][29] | job `95480200904` | failure قبل التنفيذ؛ runner_id=0؛ steps=0 |
| Mobile Android CI/CD | [32060318319][30] | job `95480218440` | failure قبل التنفيذ؛ runner_id=0؛ steps=0 |
| Preview Deploy | [32060318363][31] | job `95480242914` | failure قبل التنفيذ؛ runner_id=0؛ steps=0 |

إعادة التشغيل لم تُظهر أي source-level failure جديد، ولم تغيّر الحكم المحلي: quality gate وfull backend regression وsecret guard ما زالت ناجحة محلياً، بينما GitHub runner allocation غير متاح. لذلك لا يوجد إصلاح آمن إضافي داخل الكود يمكنه تحويل هذه النتائج إلى PASS، ولا يجوز تعطيل jobs أو تغيير شروطها لإخفاء الحظر.

[27]: https://github.com/samertts/gula-platform/actions/runs/32060318297 "IAM Hardening Gate — SHA 33664e8d rerun"
[28]: https://github.com/samertts/gula-platform/actions/runs/32060318338 "Changed Files Quality Gate — SHA 33664e8d rerun"
[29]: https://github.com/samertts/gula-platform/actions/runs/32060318515 "Security Hardening — SHA 33664e8d rerun"
[30]: https://github.com/samertts/gula-platform/actions/runs/32060318319 "Android CI/CD — SHA 33664e8d rerun"
[31]: https://github.com/samertts/gula-platform/actions/runs/32060318363 "Preview Deploy — SHA 33664e8d rerun"
