# GULA — P0 Identity & Account Lifecycle — Command 02

**التاريخ:** 15 آب 2026
**الفرع:** `security/p0-bootstrap-alembic`
**النطاق:** Backend canonical NIAM، Account Request، Verification، Account lifecycle، واجهة Web/PWA، واختبارات read-only/local.
**القرار:** `ACCOUNT_LIFECYCLE = PARTIAL` و`SAFE_STOP` قبل Command 03.

## 1. الملخص التنفيذي

أُنجز تنفيذ Command 02 داخل المسار canonical الموجود في NIAM دون إنشاء نموذج Person أو Identity أو Account موازٍ، ودون حذف أي legacy model. أصبحت دورة الطلب والحساب ممثلة بحالات وانتقالات صريحة، وأضيفت مسارات فعلية للمراجعة والتحقق والاعتماد والتفعيل والتعليق والقفل وإعادة التفعيل والإلغاء النهائي. كما أضيفت واجهة Account Request حقيقية في بوابة التسجيل ولوحة إدارة الطلبات داخل صفحة NIAM Lifecycle، مع إبقاء التسجيل الذاتي العام مغلقاً.

لم يُعتبر المسار كاملاً end-to-end لأن موفر التحقق الرسمي للهوية غير متصل في هذه البيئة. لذلك لا يصدر النظام activation token ولا يسمح بتحويل الحساب إلى `ACTIVE` ما لم تثبت `identity_verified` عبر provider canonical متصل. هذا السلوك مقصود ومغلق افتراضياً، وليس فشلاً مخفياً أو fake verification.

## 2. Changes Made

| المجال | التنفيذ |
|---|---|
| Account states | إضافة `requested`, `pending_verification`, `verified`, `pending_approval`, `approved`, `active`, `suspended`, `locked`, `deactivated`, `rejected`, `expired`. |
| State machine | مصفوفة `LEGAL_TRANSITIONS` صريحة تمنع الانتقال المباشر من `pending_verification` إلى `active`. |
| Account Request | حالات `pending_review`, `under_review`, `pending_verification`, `verified`, `pending_approval`, `approved`, `rejected`, `expired`, `cancelled`. |
| Verification | OTP عبر NotificationService الموجود فقط، مع TTL، single-use، attempt limit، replay protection، وعدم تسجيل الرمز أو المستلم في logs/audit. |
| Account creation | إنشاء Person ثم Identity ثم Account فقط بعد verification وapproval، مع duplicate prevention وrow locking وidempotent retry. |
| Approval | الاعتماد لا ينشئ Role أو Membership أو Workspace ولا يمنح صلاحية إضافية تلقائياً. |
| Activation | activation token hashed وsingle-use، مع password policy، وفحص `identity_verified` قبل التفعيل. |
| Suspension/Lock | دعم التعليق اليدوي، القفل الأمني/الإداري، التعليق المؤقت عبر `suspended_until`، إعادة التفعيل، والإلغاء النهائي. |
| Authorization | governance mutations تعتمد على `NiamActor` وSession وMembership نشطة داخل `NIAM_GOVERNANCE_ORGANIZATION_ID`، وتفشل مغلقاً عند غياب الإعداد. |
| Tenant isolation | mutation للحساب الهدف تتحقق من Membership نشطة داخل governance organization؛ لا يقبل العميل organization أو facility أو workspace كسلطة نهائية. |
| Frontend | إضافة Account Request form، verification/pending/activation states، وAccount Requests tab في `LifecyclePage` دون Mock Authentication أو Legacy fallback. |
| Privacy | إزالة recipient PII من NotificationService failure logs. |

الأدلة المصدرية موجودة في خدمة دورة الحساب [1]، وخدمة الطلب والتحقق [2]، ومسارات API [3]، وصفحة التسجيل [4]، وصفحة Lifecycle [5].

## 3. Account State Machine

| الحالة الحالية | الانتقالات المسموحة | الحارس الرئيسي |
|---|---|---|
| `requested` | `pending_verification`, `rejected`, `expired` | النظام بعد إنشاء الطلب أو job expiry |
| `pending_verification` | `verified`, `rejected`, `expired` | provider verification فقط أو governance rejection |
| `verified` | `pending_approval`, `rejected`, `expired` | خدمة lifecycle بعد نجاح التحقق |
| `pending_approval` | `approved`, `rejected`, `expired` | governance actor مصرح |
| `approved` | `active`, `deactivated` | activation flow بعد identity verification أو governance deactivation |
| `active` | `suspended`, `locked`, `deactivated` | governance actor أو security control |
| `suspended` | `active`, `deactivated` | governance actor مع audit |
| `locked` | `active`, `deactivated` | security/governance actor مع audit |
| `rejected` | لا انتقالات | حالة نهائية |
| `expired` | لا انتقالات | حالة نهائية |
| `deactivated` | لا انتقالات | حالة نهائية غير قابلة لإعادة التفعيل |

كل transition يغير حالة الخادم فقط بعد تحقق الانتقال، ولا يثق في `status` أو `actor_id` أو scope مقدم من العميل.

## 4. APIs Changed

| المسار | نطاق الوصول | الغرض |
|---|---|---|
| `POST /niam/account-requests/` | Public request-only | إنشاء طلب مراجعة؛ لا ينشئ حساباً. يتطلب `Idempotency-Key` وrate limit. |
| `POST /niam/account-requests/{id}/verification/start` | Public, generic response | بدء إرسال OTP عبر provider الموجود؛ لا يكشف وجود الطلب أو بيانات الاتصال. |
| `POST /niam/account-requests/{id}/verification/confirm` | Public, rate limited | تحقق OTP، single-use، expiry، replay protection. |
| `GET /niam/account-requests/` | Governance actor | قائمة sanitized للطلبات. |
| `POST /niam/account-requests/{id}/review` | Governance actor | نقل الطلب إلى `under_review`. |
| `POST /niam/account-requests/{id}/approve` | Governance actor | إنشاء Person/Identity/Account بعد verification، ووضع الطلب `approved` والحساب `approved`. |
| `POST /niam/account-requests/{id}/reject` | Governance actor | رفض الطلب مع تخزين reason مشفراً. |
| `POST /niam/account-requests/{id}/expire` | Governance actor/job boundary | إنهاء الطلب المنتهي. |
| `POST /niam/account-requests/{id}/activation-token` | Governance actor | إصدار token عبر provider فقط بعد identity verification؛ لا يعيد token في response. |
| `POST /niam/account-requests/{id}/activate` | Public token flow | تفعيل أحادي الاستخدام بعد approval و`identity_verified`. |
| `POST /niam/account-requests/accounts/{uuid}/suspend` | Governance actor | تعليق يدوي أو مؤقت مع reason وscope. |
| `POST /niam/account-requests/accounts/{uuid}/lock` | Governance/security actor | قفل أمني أو إداري مع reason. |
| `POST /niam/account-requests/accounts/{uuid}/reactivate` | Governance actor | إعادة تفعيل من suspended/locked فقط. |
| `POST /niam/account-requests/accounts/{uuid}/deactivate` | Governance actor | إلغاء نهائي غير قابل لإعادة التفعيل. |

لا تعيد هذه المسارات ORM models مباشرة؛ serializers تعيد حقولاً bounded ولا تشمل contact ciphertext أو password أو OTP أو token hash.

## 5. Models and Migration

تم تعديل النماذج canonical التالية:

| النموذج | التعديل |
|---|---|
| `Account` | حالات lifecycle الجديدة و` suspended_until` للتعليق المؤقت. |
| `AccountCreationRequest` | حالات الطلب، verification metadata، expiry، وactivation token hash/expiry. |
| `Person`, `Identity`, `Membership`, `Organization`, `Facility`, `Workspace` | لم تُنشأ نسخ بديلة؛ استُخدمت النماذج الموجودة. |

أُنشئت migration صغيرة قابلة للعكس [6]، revision `20260815_0023`، فوق `20260815_0022`. أضيفت الحقول الجديدة وصلاحيتا catalog:

```text
identity.account_request.manage
identity.account.manage
```

لا تُنشئ migration أي RoleAssignment تلقائياً. يجب أن يتم إسناد الصلاحية داخل governance organization بواسطة إجراء بشري معتمد.

تم اختبار:

```text
upgrade 0023 → downgrade 0022 → upgrade 0023
```

على قاعدة SQLite مؤقتة فقط، ونجح الاختبار، مع بقاء Alembic على رأس واحد هو `20260815_0023`.

## 6. Security Controls

يستخدم الطلب `Idempotency-Key` hashed، وتمنع duplicate pending requests على blind-index للاتصال. تستخدم OTP digest داخل cache بمدة 15 دقيقة، وبحد أقصى خمس محاولات، وتحذف بعد النجاح. لا يُعاد قبول OTP بعد الاستخدام ولا يُعرض في response أو audit. لا يسجل NotificationService recipient عند فشل الإرسال.

تُنفذ governance mutations فقط بواسطة `NiamActor` active/unlocked/session صالحة، وتحتاج governance organization مضبوطة على الخادم. إذا كان `NIAM_GOVERNANCE_ORGANIZATION_ID` غائباً فالنتيجة `503` ولا يوجد fallback إلى دور ثابت أو global mutation. كما يتحقق account mutation من Membership نشطة للحساب الهدف داخل نفس governance organization، ويمنع cross-tenant access.

يبقى `PUBLIC_SELF_REGISTRATION_ENABLED` مغلقاً. لم يتم تفعيل National ID، أو OCR، أو NFC، أو biometric verification. لا يوجد fake provider ولا bypass من واجهة Web.

## 7. Audit Events

تسجل المنظومة أحداث الطلب والتحقق والحساب، بما في ذلك:

```text
account_request_submitted
account_request_under_review
account_request_pending_verification
account_request_verification_failed
account_request_verified
account_request_pending_approval
account_request_approved
account_request_rejected
account_request_expired
account_created
account_activated
account_suspended
account_locked
account_unlocked
account_disabled
```

تتضمن الأحداث actor وtarget وdecision/reason وrequest correlation حيث يتوفر، ولا تتضمن password أو OTP أو token أو ciphertext أو contact plaintext.

## 8. Tests and Validation

| البوابة | النتيجة |
|---|---:|
| Backend non-integration suite | **2620 passed**, 41 integration tests مستثناة في التشغيل الأولي بسبب قاعدة غير مهيأة. |
| Backend integration suite على SQLite migrated temp DB | **40 passed, 1 skipped**؛ التخطي متعلق باعتماد clinical gateway غير متصل. |
| Command 02 targeted identity/request tests | **24 passed**، مع نجاح اختبارات account request القديمة وmembership contracts. |
| Frontend typecheck | **ناجح**. |
| Frontend Vitest | **50 passed**. |
| Frontend production build/PWA | **ناجح**. |
| Ruff على الملفات المعدلة | **ناجح**. |
| Python compileall | **ناجح**. |
| Alembic head | **رأس واحد: 20260815_0023**. |
| SQLite migration upgrade/downgrade/upgrade | **ناجح**. |
| `git diff --check` | **ناجح قبل commit النهائي**. |

## 9. Cross-platform Status

| المنصة | حالة Command 02 |
|---|---|
| Web/PWA | `IMPLEMENTED` للـAccount Request، verification/pending/activation UI، ولوحة governance lifecycle. تم التحقق بـtypecheck/tests/build. |
| Android | `UNVERIFIED` في هذه البيئة؛ تغييرات P1 السابقة موجودة، لكن Android SDK غير متاح لتشغيل compileDebugKotlin. |
| Flutter Desktop | `UNVERIFIED`؛ Flutter SDK غير متاح محلياً. |
| iOS | `NOT_BUILT/UNVERIFIED`؛ لا توجد بيئة Xcode في sandbox. |

لا توجد دعوى parity غير مثبتة بين Web وAndroid وFlutter وiOS.

## 10. Remaining Gaps

أهم الفجوات التي تمنع تصنيف الدورة `COMPLETE` هي أن provider canonical للهوية غير متصل، ولذلك يبقى الحساب بعد approval في `approved` ولا يمكن إصدار activation token أو الوصول إلى `active` حتى يكتب provider الموثوق `identity_verified`. كما يجب إعداد `NIAM_GOVERNANCE_ORGANIZATION_ID` وربط governance account بـMembership وRole/Permission من خلال إجراء إداري معتمد.

يجب في staging اختبار email/SMS provider الحقيقي، Redis مشترك متعدد العمال، session cookie/CSRF policy، job expiry الدوري، وtenant matrix للحسابات من منظمات مختلفة. كما يجب تشغيل Android/Flutter CI على بيئة SDK فعلية ومراجعة migration على PostgreSQL staging قبل أي release.

## 11. Human Approval Required

يلزم اعتماد بشري قبل أي إجراء خارجي: مراجعة migration `0023` وتطبيقها على staging، إنشاء governance organization وربط permissions/roles، توصيل provider الرسمي للهوية، ضبط secrets وRedis/Notification providers، تشغيل CI للجوال، ثم تنفيذ deployment staging. لا يجوز تطبيق migration أو تفعيل provider أو التسجيل العام على production من هذا التقرير.

## 12. Production Actions NOT Performed

لم يتم تنفيذ production deployment، ولا production database migration، ولا public self-registration activation، ولا National ID/OCR/NFC/Biometrics activation، ولا push، ولا merge، ولا إنشاء PR جديد، ولا تغيير حماية الفروع. working tree يحتوي تغييرات Command 02 والتقرير لتتم مراجعتها وحفظها في commit محلي بعد موافقة المستخدم.

## References

[1]: ../../backend/app/identity/services/account_lifecycle_service.py "Canonical account lifecycle state machine"
[2]: ../../backend/app/identity/services/account_request_service.py "Account request, verification, approval and activation service"
[3]: ../../backend/app/identity/api/account_requests.py "Account request lifecycle API"
[4]: ../../frontend-v3/src/pages/auth/RegisterPage.tsx "Review-gated account request frontend"
[5]: ../../frontend-v3/src/pages/niam/LifecyclePage.tsx "NIAM lifecycle governance frontend"
[6]: ../../backend/migrations/versions/20260815_0023_account_request_lifecycle.py "Reversible Command 02 migration"
[7]: ../../backend/tests/identity/test_account_request_lifecycle_command02.py "Command 02 lifecycle and contract tests"
