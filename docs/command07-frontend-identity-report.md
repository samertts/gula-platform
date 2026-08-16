# GULA — Command 07
## Frontend + Cross-Platform Identity Integration

### القرار النهائي

> **FRONTEND_IDENTITY_PARTIAL**

تم تنفيذ دورة هوية موحدة ومتكاملة فعلياً داخل `frontend-v3` وPWA للمسارات التي تملك عقود Backend مثبتة. بقي القرار **PARTIAL** لا **COMPLETE** لأن تكافؤ Android وiOS وFlutter/Desktop غير مثبت ببناءات فعلية في هذا المستودع، ولأن بعض قدرات مركز الأمان المتقدمة لا تملك API شخصية كاملة بعد، إضافة إلى أن Persian يستخدم حالياً fallback إلى English بدلاً من resource فارسي مستقل.

لم يتم نشر Production، ولم تعدل قاعدة بيانات Production أو feature flags، ولم يُفعّل Public Registration أو Government Identity أو OCR/NFC/Biometrics، ولم يحدث Automatic Merge، ولم يبدأ Command 08.

## 1. Frontend Identity Inventory

| Capability | الحالة الحالية | التنفيذ أو الدليل |
|---|---|---|
| Register | PARTIAL | أصبح المسار نموذج **Account Request** فقط؛ لا ينشئ حساباً ولا يصدر جلسة. التسجيل العام ما زال مغلقاً. |
| Account Request | PASS | يستخدم `POST /niam/account-requests/` مع `Idempotency-Key`، ويعرض accepted/pending/failure. |
| Verification | PARTIAL | توجد عقود request/confirm والتحويل إلى حالة `VERIFYING`، لكن لا توجد رحلة UI مستقلة كاملة لرمز التحقق بعد login/register. |
| Activation | BACKEND_DEPENDENCY | التفعيل قرار مراجعة خادمي؛ الواجهة تعرض Pending Review ولا تنفذ activation. |
| Login | PASS/PARTIAL | يمر عبر `/login` وHttpOnly cookies، مع تصنيف حالات 401/403/429/5xx/Offline. MFA الإجباري للـprivileged account يظهر كـverification required وفق استجابة الخادم. |
| Logout | PASS | `/logout` ثم تنظيف كامل للـidentity/workspace/error state. |
| Session Expired | PASS | interceptor يحاول refresh مرة واحدة فقط للمسار المحمي؛ عند الفشل يصدر `gula:session-expired`، يمسح كل state، ولا يستخدم بيانات قديمة أو mock fallback. |
| Refresh | PASS بالنسبة لعقد `/auth/refresh` | يتم الاعتماد على HttpOnly refresh cookie؛ لا تحفظ الواجهة refresh/access tokens. |
| Revocation | PARTIAL | إبطال الجلسة الحالية عبر logout، وإبطال الكل عبر session endpoint عندما يعيد الخادم `account_id`. اكتمال الإبطال الفوري لكل تغييرات العضوية والدور يحتاج اختبار Staging حي. |
| Recovery | PASS/PARTIAL | صفحة `/recover` تستخدم `/auth/forgot-password` برسالة لا تكشف وجود الحساب، وتعرض success/failed/expired. `/auth/reset-password` موجود كعقد، لكن صفحة إدخال reset token الكاملة تحتاج استكمالاً منفصلاً. |
| Security | PASS/PARTIAL | Security Center شخصي يعرض الحالة الأمنية، MFA، أجهزة MFA، sessions عندما يتوفر account context، وLogout All. |
| Devices | PARTIAL | أجهزة MFA مدعومة عبر `/mfa/devices`. قائمة أجهزة NIAM العامة للمستخدم غير متاحة؛ لا يتم اختراعها. |
| MFA/Passkey | PARTIAL | `/mfa/status` وdevices وTOTP/WebAuthn contracts موجودة. Security Center يعرض الحالة والأجهزة؛ تفعيل WebAuthn الكامل يحتاج UI ceremony/browser integration وسياسة اعتماد إضافية. |
| Workspace Selection | PASS | selector يعتمد على `AuthContext.availableWorkspaces` ويعرض اختياراً صريحاً. لا يوجد auto-select من ترتيب القائمة. |
| Workspace Switch | PASS | `switchWorkspace` يرسل ID إلى Backend وينتظر `WorkspaceContextResponse` authoritative ثم يعيد تحميل memberships/effective permissions. |
| Membership | PASS/PARTIAL | صفحة `/memberships` تعرض Active/Pending/Suspended/Expired/Revoked مع organization/facility/workspace/scope/source/status. لا تسمح بالتعديل المحلي. |
| Unauthorized 401 | PASS | جلسة منتهية/مبطلة → تنظيف وإعادة مصادقة. |
| Forbidden 403 | PASS | رسالة صلاحية موحدة بلا اعتبار الواجهة حاجزاً أمنياً. |
| Conflict 409 | PASS | رسالة تعارض سياق وإعادة تحميل آمنة. |
| Rate Limit 429 | PASS | رسالة انتظار وإعادة محاولة آمنة. |
| Server 5xx | PASS | رسالة خدمة غير متاحة مع Retry آمن. |
| Offline | PASS | لا تعرض الواجهة بيانات مخزنة قديمة على أنها حالية. |

## 2. Auth State Model

تم إنشاء `frontend-v3/src/auth/authState.ts` بنموذج موحد للحالات التالية:

```text
UNKNOWN
LOADING
UNAUTHENTICATED
VERIFYING
PENDING
AUTHENTICATED
WORKSPACE_REQUIRED
AUTHORIZED
SESSION_EXPIRED
SUSPENDED
LOCKED
ERROR
```

`AuthContext` أصبح يعرض `state`, `error`, `workspace`, `workspaceContext`, `availableWorkspaces`, `memberships`, و`effectivePermissions` بالإضافة إلى الدوال server-backed. بقيت `isAuthenticated` و`isLoading` كواجهات توافقية للصفحات القديمة، لكن مصدر القرار الجديد هو `state` وليس boolean محلياً فقط.

إذا أعاد الخادم Workspace واحداً، يتم إرسال switch صريح إلى الخادم ثم اعتماد الـcontext الذي يرجعه. وإذا أعاد عدة Workspaces، تصبح الحالة `WORKSPACE_REQUIRED` ولا يتم اختراع سياق فعّال. إذا لم توجد Workspaces، تبقى الهوية `AUTHENTICATED` دون منح صلاحية Workspace غير موجود.

## 3. Session Integration

تم تحسين `api/client.ts` بحيث لا يحاول refresh لطلبات login/register/recovery نفسها، ولا يعيد التوجيه مباشرة من طبقة API. عند 401 لمسار محمي فقط، يحاول `/auth/refresh` مرة واحدة مع `withCredentials`; عند الفشل يرسل حدث انتهاء الجلسة إلى AuthContext.

عند انتهاء أو إبطال الجلسة، يتم مسح المستخدم والعضويات والصلاحيات ومساحات العمل والسياق وdemo markers، وتعود API mode إلى `live`. لا يوجد token في `localStorage`، ولا يتم استعمال `user` مخزن أو `legacy fallback` لإبقاء الشاشة السريرية معروضة.

## 4. Workspace Integration

تم تحويل `WorkspaceSelector` من قارئ API مستقل إلى مستهلك لـ`AuthContext`. التبديل يمر عبر `switchWorkspace` الموحد، ويحافظ selector على السياق السابق إذا رفض الخادم العملية. request barriers أصبحت تسمح فقط بعقود workspace/session/MFA/account-request المعلنة، وتبقي القراءات والكتابات السريرية المباشرة محجوبة عندما لا يكون لها عقد معتمد في الواجهة.

الواجهة لا تقبل `organization_id` أو `facility_id` أو `workspace_id` كـauthoritative context. الـIDs تستخدم كمدخل لطلب الخادم فقط، والـcontext النهائي هو استجابة الخادم.

## 5. Registration, Login, Recovery UX

أصبح `/register` نموذج Account Request حقيقياً يرسل `display_name`, `email`, `phone`, و`requested_account_type` مع idempotency key. يعرض `Pending Review` بعد HTTP 202 ولا يستطيع تفعيل Public Registration أو إنشاء جلسة.

صفحة login تصنّف الرسائل إلى invalid credentials، verification/MFA required، locked، suspended، rate limited، service unavailable، وoffline. الرسائل لا تكشف ما إذا كان البريد أو الهاتف مسجلاً. أضيف رابط recovery إلى `/recover`.

## 6. Security Center

صفحة `/security` أصبحت متاحة ضمن المسار المصادق بدلاً من قصرها على `RoleGuard` الإداري، لأن عرض حماية الحساب الشخصي ليس بديلاً عن Backend authorization. وتعرض:

| العنصر | مصدره |
|---|---|
| MFA enabled وMFA devices | `/mfa/status` و`/mfa/devices` |
| Current NIAM sessions | `/niam/sessions/account/{account_id}` عندما يعيد الخادم account context |
| Logout All Devices/Sessions | `/niam/sessions/account/{account_id}/terminate-all` |
| Security status/checks | `/security/status` مع احترام أن التفاصيل الإدارية لا تظهر للحساب العادي |
| Passkey/WebAuthn indicator | نوع جهاز MFA فقط؛ لا يتم الادعاء بإتمام browser ceremony من هذه الصفحة |

لا تعرض الصفحة secrets أو access/refresh tokens. عدم توفر API شخصية للأحداث الحديثة أو قائمة أجهزة NIAM العامة موثق كـ`BACKEND_DEPENDENCY` بدلاً من اختراع بيانات.

## 7. Memberships

أضيف المسار `/memberships` ورابطه في navigation. الصفحة تعرض الحالات Active/Pending/Suspended/Expired/Revoked، وتعرض organization وfacility وworkspace وscope/source وexpiry. لا توجد أزرار تعديل membership من هذه الصفحة، وأي mutation يبقى في Backend authorization والعقود القائمة.

## 8. Localization and Accessibility

تم الحفاظ على اللغات المسجلة: العربية العراقية، العربية الفصحى، English، Kurdish، Turkmen، Assyrian، وPersian code. أضيف `nav.memberships` إلى resources العربية والإنجليزية والكردية والتركمانية والسريانية. ما زال Persian يستخدم fallback إلى English في `i18n/index.ts`، ولذلك لا يصح إعلان ترجمة فارسية كاملة.

تم الحفاظ على RTL/LTR عبر `LocaleContext.isRTL` بدلاً من اختبار locale واحد فقط، وأصبح تبديل اللغة في DashboardLayout يمر على اللغات المسجلة ولا يمسح session أو workspace context. عناصر workspace/error/loading تستخدم `role=status` و`role=alert`، والـselector قابل للوحة المفاتيح، ورسائل الخطأ لا تعتمد على اللون وحده.

Adaptive UI الموجود مسبقاً يغطي تفضيلات color blindness وlow vision وlarge text وhigh contrast وreduced motion وscreen reader وkeyboard وlarger touch targets عبر AccessibilityContext. لم يتم تغيير endpoint التفضيلات أو تخزين بيانات صحية في browser storage.

## 9. API Mapping

| UI flow | API/request | Response/auth | Context/error/audit |
|---|---|---|---|
| Account Request | `POST /niam/account-requests/` + `Idempotency-Key` | 202 accepted review-only | لا جلسة ولا activation؛ Backend intake/rate-limit/audit |
| Login | `POST /login` body email/password | HttpOnly access/refresh cookies + user | 401/403/429 مصنفة؛ audit في Backend |
| Session restore | `GET /session` | user/session reflected | 401 → unauthenticated؛ offline → ERROR دون stale UI |
| Refresh | `POST /auth/refresh` cookie | rotated cookies | retry once؛ failure → SESSION_EXPIRED/revocation UX |
| List memberships | `GET /niam/memberships/me` | membership list | permissions reflected server-side |
| Effective permissions | `GET /niam/roles/effective` | organization-scoped permissions | UX hint only؛ Backend remains authority |
| List workspaces | `GET /niam/workspaces` | eligible workspaces | no client auto-select |
| Switch workspace | `POST /niam/workspaces/{id}/switch` | WorkspaceContextResponse | server-authoritative context/version/audit |
| Current sessions | `GET /niam/sessions/account/{account_id}` | session UUID/id list | requires account context from server |
| Logout all | `POST /niam/sessions/account/{account_id}/terminate-all` | success | backend account ownership check/audit |
| MFA status/devices | `GET /mfa/status`, `GET /mfa/devices` | mfa_enabled/devices | no secrets rendered |
| Recovery request | `POST /auth/forgot-password` | non-enumerating message | sensitive verification stays server-side |
| Security summary | `GET /security/status` | public status or admin checks | admin-only detail respected |

## 10. Cross-Platform Matrix

| Capability | Web | PWA | Android | iOS | Flutter/Desktop | Status | Evidence |
|---|---|---|---|---|---|---|---|
| Login/session lifecycle | PASS | PASS | NOT_BUILT | NOT_BUILT | UNVERIFIED | PARTIAL overall | Web/PWA `AuthContext`, interceptor، tests/build؛ لا mobile builds في repo الحالي |
| HttpOnly web session | PASS | PASS | NOT_BUILT | NOT_BUILT | UNVERIFIED | PARTIAL | `withCredentials` وno localStorage tokens |
| Mobile secure storage | N/A | N/A | NOT_BUILT | NOT_BUILT | N/A | NOT_BUILT | لا توجد toolchains/app source مثبتة هنا |
| Refresh/revocation | PASS | PASS | NOT_BUILT | NOT_BUILT | UNVERIFIED | PARTIAL | `/auth/refresh` وsession-expired event؛ لا cross-platform runtime evidence |
| Workspace selection/switch | PASS | PASS | NOT_BUILT | NOT_BUILT | UNVERIFIED | PARTIAL | WorkspaceSelector + API tests |
| Membership display | PASS | PASS | NOT_BUILT | NOT_BUILT | UNVERIFIED | PARTIAL | `/memberships` page + live membership contract |
| MFA/Passkey | PARTIAL | PARTIAL | NOT_BUILT | NOT_BUILT | UNVERIFIED | PARTIAL | `/mfa/status` وdevices فقط؛ WebAuthn ceremony UI ليست مكتملة |
| Deep links | UNVERIFIED | UNVERIFIED | NOT_BUILT | NOT_BUILT | UNVERIFIED | UNVERIFIED | لا توجد builds/toolchains أو manifests كافية لإثبات المسار |
| RTL/LTR/responsive | PASS | PASS | NOT_BUILT | NOT_BUILT | UNVERIFIED | PARTIAL | LocaleContext، responsive web tests/build |

## 11. Tests and Build

| الفحص | النتيجة |
|---|---:|
| Frontend official `pnpm test` | **61 tests passed في 17 ملفاً** |
| AuthState unit tests | **3 passed** |
| Error UX unit tests | **4 passed** |
| WorkspaceSelector + accessibility | **8 passed** |
| Frontend typecheck | **PASS** |
| Frontend lint | **PASS** |
| Frontend production build + PWA generateSW | **PASS**؛ 190 precache entries |
| Backend focused identity/workspace/session tests | **13 passed** |
| Ruff على ملفات Command 06 backend المعدلة | **PASS** |
| `git diff --check` | **PASS** |

تشغيل Vitest الرسمي يستبعد `e2e/**` كما يحدد script المشروع. لم يتم حذف اختبار فاشل ولم تُستخدم suppressions عامة. تم تثبيت اعتماديات backend الناقصة داخل `backend/.venv` وفق requirements المعلنة فقط؛ لم يتغير كود Production بسبب ذلك.

## 12. Security Findings and Remaining Dependencies

| finding/dependency | القرار |
|---|---|
| Persian locale fallback إلى English | PARTIAL localization؛ يحتاج resource فارسي مستقل قبل COMPLETE |
| NIAM public device listing | BACKEND_DEPENDENCY؛ لا يوجد endpoint current-user list في `identity/api/devices.py` |
| Security recent events personal feed | BACKEND_DEPENDENCY؛ `/security/status` يعطي status عام أو admin aggregate، وليس personal event feed |
| Session current account UUID | PARTIAL؛ sessions API موجود لكن Security Center لا يستعمل legacy numeric user id كبديل |
| WebAuthn full browser ceremony | BACKEND/UI DEPENDENCY؛ endpoints begin/complete موجودة، لكن passkey UX الكامل يحتاج policy وتجربة متصفح واختبارات مناسبة |
| Android/iOS/Flutter/Desktop parity | UNVERIFIED/NOT_BUILT؛ لا توجد toolchains/build evidence في هذا المستودع |
| Frontend authorization | SAFE؛ RoleGuard/sidebar UX فقط، ولا يعتمد عليه كحاجز أمني |
| tokens/browser storage | SAFE بالنسبة للتغييرات الجديدة؛ token fields types فقط، والتخزين المستخدم marker demo/locale/theme لا tokens |
| mock identity | محصور في demo المعلن synthetic؛ مسار انتهاء session لا يعيد mock user ولا legacy session |

## 13. Human Approval Required

يلزم اعتماد بشري قبل إعلان `FRONTEND_IDENTITY_COMPLETE` للقرارات التالية: اعتماد resource فارسي مستقل، تحديد عقد personal security events وNIAM device list، اعتماد WebAuthn browser ceremony وسياسة passkeys، توفير toolchains وبناءات Android/iOS/Flutter/Desktop، وتشغيل اختبار Staging بــPostgreSQL وRedis حقيقيين لإثبات refresh rotation وrevocation وrace conditions.

لا يجب تفعيل Public Registration أو Government Identity أو OCR/NFC/Biometrics، ولا يجب استخدام أي واجهة frontend كبديل لـBackend authorization. لا يبدأ Command 08 تلقائياً.

## المراجع الداخلية

| المرجع | الغرض |
|---|---|
| `frontend-v3/src/auth/authState.ts` | Auth State Model |
| `frontend-v3/src/contexts/AuthContext.tsx` | session/workspace/membership state |
| `frontend-v3/src/api/client.ts` | refresh/error/request barriers |
| `frontend-v3/src/api/errorHandling.ts` | unified HTTP/offline classification |
| `frontend-v3/src/api/endpoints.ts` | actual frontend API contracts |
| `backend/app/identity/api/sessions.py` | session list/terminate/terminate-all contracts |
| `backend/app/identity/api/account_requests.py` | account request contract |
| `backend/app/routes/mfa.py` | MFA/TOTP/WebAuthn/device contract |
| `backend/app/routes/security.py` | security status limitations |
| `backend/app/identity/api/devices.py` | NIAM device-management limitations |
| `docs/command06-authorization-context-report.md` | Command 06 partial decision |

## 13. Cross-Platform Remediation Update

تمت معالجة الجزء القابل للتنفيذ من فجوات Flutter/mobile/desktop داخل `mobile/desktop`، وهو مشروع Flutter واحد يستهدف Android وiOS وWindows وLinux وmacOS، وليس تطبيق Desktop منفصلاً فقط.

| الفجوة | المعالجة |
|---|---|
| AuthStatus محدود | أضيف `IdentityState` المشترك بالحالات الاثنتي عشرة المطلوبة، مع إبقاء AuthStatus القديم للتوافق الانتقالي. |
| عدم وجود Workspace lifecycle | أضيف list/switch Workspace، مع رفض auto-authorize واعتماد context الذي يعيده الخادم فقط. |
| Router يعتمد boolean فقط | أضيفت guards لـunknown/loading وMFA وworkspace-required وsession-expired عبر `AuthProvider.identityState`. |
| Recovery stub | أُوصل Forgot Password فعلياً بـ`POST /auth/forgot-password` برسالة غير كاشفة. |
| عدم وجود Account Request | أضيفت صفحة `/account-request` ترسل `POST /niam/account-requests/` وتعرض Pending Review دون إصدار جلسة. |
| غياب Memberships | أضيفت `/memberships` مع status/scope/organization/facility/workspace من state الخادمي. |
| غياب Workspace UI | أضيفت `/workspace` للاختيار والتبديل الصريح مع الحفاظ على السياق السابق عند الرفض. |
| غياب Security Center | أضيفت `/security` لعرض MFA/devices/sessions وLogout All وفق account context، دون secrets. |
| refresh race/recursive refresh | أضيف single-flight refresh lock و`skipAuthRefresh` لمسار refresh نفسه. |
| desktop-only bootstrap | أصبح window manager وauto-updater وdesktop window setup مشروطاً بالمنصة؛ mobile يسمح portrait/landscape ولا ينفذ desktop updater. |
| Sidebar غير مكتمل | أضيفت روابط Memberships وWorkspace وSecurity Center. |
| localization محدودة | أضيفت supported locales: ar/en/ku/tk/syr/fa مع fallback واضح ومفاتيح الهوية الأساسية، وأضيفت الاختيارات إلى Settings. |

## 14. Cross-Platform Verification Boundary

تم تنفيذ اختبارات unit إضافية لـ`IdentityState` في `mobile/desktop/test/unit/identity_state_test.dart`، ونجح static transport security check، ونجح `git diff --check`. لم يكن Flutter SDK متاحاً داخل sandbox الحالي، لذلك لا يجوز ادعاء نجاح `flutter analyze` أو `flutter test` أو builds Android/iOS/Windows/Linux/macOS محلياً.

سيتم اعتماد التحقق النهائي من خلال CI المعلن في `.github/workflows/mobile-flutter-desktop.yml` بعد رفع commit، ويجب أن يشمل `flutter analyze` و`flutter test` وبناءات Windows/Linux/macOS. أما Android/iOS فتحتاج runners/toolchains مناسبة أو CI mobile مستقل؛ عدم وجودها يبقيهما `UNVERIFIED` حتى يتم تشغيلهما فعلياً.

حتى بعد نجاح CI، يبقى `FRONTEND_IDENTITY_PARTIAL` هو القرار الآمن إذا لم تتوفر اختبارات device حقيقية لـAndroid/iOS/deep-links وWebAuthn ceremony، أو إذا لم يثبت Staging تدوير refresh والإبطال المتزامن مع Redis/PostgreSQL حقيقيين.

## 15. Native Mobile Platform Remediation Update

تم إغلاق فجوة عدم وجود منصات أصلية داخل مشروع Flutter. أضيفت ملفات Android وiOS الرسمية عبر Flutter 3.44، مع بقاء application id `org.gula.gula_desktop` واسم الحزمة الحالي. أضيف `gula://` custom URL scheme إلى Android Manifest وiOS Info.plist لفتح مسارات الهوية عبر deep links؛ لم يتم الادعاء بإعداد Universal Links/App Links موثقة على نطاق Production.

أضيف workflow مستقل `.github/workflows/mobile-flutter-native.yml` يقوم بـ`dart analyze` و`dart format` و`flutter test`، ثم يبني Android debug APK وiOS debug build بدون code signing. وبذلك أصبحت Android وiOS قابليتين للبناء في CI، مع فصل signing/notarization عن هذا التحقق الآلي.

التحقق المحلي باستخدام Flutter 3.44: **Flutter tests passed (14 tests)**، و`flutter analyze --no-fatal-infos --no-fatal-warnings` لم يعثر على أخطاء compile/analyze، لكنه يعرض ملاحظات lint قديمة على مستوى المستودع. كما تم إصلاح Flutter template test الذي كان يستدعي `MyApp` غير موجود.

يبقى تحقق جهاز فعلي وApp Links/Universal Links production signing خارج sandbox، لذلك لا يتم الادعاء بتماثل device-runtime الكامل أو جاهزية النشر في المتاجر. القرار الآمن بعد هذه المعالجة يعتمد على نجاح native CI، مع بقاء `FRONTEND_IDENTITY_PARTIAL` إلى حين إثبات device tests وWebAuthn ceremony وStaging revocation الحي.
