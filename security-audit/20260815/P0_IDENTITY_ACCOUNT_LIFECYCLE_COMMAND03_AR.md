# GULA — P0 Identity & Account Lifecycle — Command 03

**العنوان:** Verification + Identity Assurance
**التاريخ:** 15 آب 2026
**الفرع:** `security/p0-bootstrap-alembic`
**الحالة:** `VERIFICATION_PARTIAL` مع `SAFE_STOP` قبل Command 04

## 1. الملخص التنفيذي

أُنجزت بنود Command 03 الممكنة داخل المستودع دون تفعيل موفر هوية حكومي أو OCR أو NFC أو biometrics، ودون استخدام بيانات وهمية أو تغيير production. تم تثبيت state machine canonical لسجلات التحقق، وتوسيع طبقة assurance مع حالات `sent` و`locked`، وربط contact verification الناجح بسجل `VerificationRecord` minimal عند إنشاء الحساب. كما تم تقوية OTP legacy وAccount Request ضد brute force وreplay وresend abuse وفشل مزود الإشعارات، وإضافة واجهات واضحة لحالات الفشل والقفل وعدم توفر المزود.

لا يمكن تصنيف الطبقة `VERIFICATION_COMPLETE` لأن موفر الهوية الرسمي غير متصل، ولا توجد adapters حقيقية لـprofessional registry أوorganization registry أوgovernment registry. وبقيت Passkey/WebAuthn مصنفة كـMFA/authentication فقط، وليس كإثبات هوية وطنية أو رفعاً تلقائياً لمستوى assurance.

## 2. Verification Inventory

| القدرة | التصنيف | النتيجة الفعلية |
|---|---|---|
| Email verification | `PARTIAL` | مسار `/auth/verification` موجود ويستخدم NotificationService وdigest في cache، لكنه legacy User path وليس canonical VerificationRecord end-to-end. |
| Phone/SMS OTP | `PARTIAL` | Account Request وlegacy verification يدعمان OTP digest وTTL ومحاولات محدودة؛ أضيف resend throttling وdurable lock، لكن channel verification لا يثبت الهوية الوطنية. |
| Canonical contact evidence | `PARTIAL` | يُنشأ VerificationRecord من نوع `contact` بعد account approval عند نجاح OTP، بمستوى L1 وminimal evidence. |
| Official identity | `NOT_CONFIGURED` | يوجد provider protocol وNotConnectedProvider وسياسة L2، ولا يوجد adapter رسمي أو credentials أو route حكومي موصول. |
| Professional verification | `NOT_CONFIGURED` | توجد أنواع وسجلات للمهنة، ولا يوجد Registry provider أو workflow موصول. |
| Organization verification | `NOT_CONFIGURED` | يوجد record type، ولا يوجد provider/evidence workflow مستقل موصول. |
| Government registry | `NOT_CONFIGURED` | لا توجد بيئة أو أسرار أو endpoint رسمي مثبت؛ تبقى dependency خارجية. |
| OCR | `BLOCKED` | لم يُفعّل ولم يُعامل كنجاح. |
| NFC | `BLOCKED` | لم يُفعّل ولم يُربط بالهوية الوطنية. |
| Biometrics | `BLOCKED` | لا يوجد تخزين templates أو تصميم قانوني/أمني معتمد؛ لم يُفعّل. |
| Passkey/WebAuthn | `IMPLEMENTED` للمصادقة/MFA فقط | MFA routes وMFAService يدعمان WebAuthn، ولا يغيران `identity_verified` أو assurance الحكومي. |
| Device biometrics | `UNVERIFIED` | لا يوجد مسار Backend موصول يربطه بهوية وطنية؛ لا يُعامل كـIdentity Assurance. |

جرد الأدلة التفصيلي محفوظ في [1].

## 3. Identity Assurance Separation

تطبق المنصة الفصل التالي:

> **Contact Verification لا يساوي Identity Verification، وIdentity Verification لا يساوي Professional أو Government Verification، وكل ذلك منفصل عن Authentication.**

OTP للبريد أو الهاتف يثبت التحكم في وسيلة اتصال عند نجاحه، ويمنح `L1` فقط. التحقق الرسمي من الهوية، عند توصيل provider معتمد لاحقاً، هو الذي يمكن أن ينتج `official_identity` و`L2`. التحقق المهني والمؤسسي لهما مستويات مستقلة. لا تُقبل قيمة `assurance_level` أو `identity_verified` من Frontend كقيمة authoritative، ولا ينشئ assurance وحده Role أوMembership أوWorkspace.

## 4. Verification State Machine

أصبحت `VerificationRecordService` تدعم الانتقالات التالية:

| الحالة الحالية | الانتقالات المسموحة |
|---|---|
| `not_started` | `sent`, `pending` |
| `sent` | `pending`, `in_progress`, `failed`, `expired`, `locked` |
| `pending` | `in_progress`, `failed`, `expired`, `locked` |
| `in_progress` | `verified`, `failed`, `requires_review`, `expired`, `locked` |
| `verified` | `expired`, `revoked` |
| `failed` | `sent`, `pending`, `locked` |
| `locked` | `requires_review`, `expired` |
| `requires_review` | `verified`, `failed`, `locked` |
| `expired` أو `revoked` | لا انتقالات |

كل حالة غير `verified` تعطي `L0`، ولا يمكن الانتقال من `locked` مباشرة إلى `verified`. الانتقال إلى `verified` يتطلب أن يكون السجل في مسار Backend قانوني، وتُسقط assurance إلى `L0` عند expiry أو lock أو revoke.

## 5. OTP and Contact Verification Controls

تم تقوية `/auth/verification` وAccount Request OTP كما يلي:

| الضابط | التنفيذ |
|---|---|
| Cryptographic code | استخدام `secrets.randbelow` لرمز من ستة أرقام. |
| At-rest protection | تخزين SHA-256 digest فقط، وليس الرمز plaintext. |
| Short expiry | TTL قدره 15 دقيقة. |
| Single use | حذف digest ومحاولة العداد بعد نجاح التحقق. |
| Replay protection | إعادة استخدام الرمز بعد النجاح مرفوض، والطلب المقفول يعيد 429. |
| Attempt limit | خمس محاولات؛ بعدها يُحذف الرمز ويُحفظ `verification_locked_at` وreason code. |
| Resend throttling | حد resend في نافذة زمنية قصيرة، مع عدم إعادة ضبط brute-force counter عند resend. |
| Rate limiting | الإبقاء على `rate_limit_auth` في endpoints، مع counter لكل identifier/request. |
| Provider failure | لا يُخزن OTP ولا يُعرض `demo_code` عند فشل NotificationService. |
| Enumeration resistance | الطلب العام يعيد رسالة موحدة للمعرف غير الموجود والموجود والمقفول. |
| Audit privacy | لا يسجل OTP أو password أو token أو recipient PII أو raw payload. |
| Durable lock | حفظ المحاولات والقفل وfailure reason في AccountCreationRequest، وليس في cache فقط. |

تمت إضافة اختبارات مباشرة لـenumeration، resend throttling، provider failure، brute-force lock، وsingle-use replay في [2].

## 6. Evidence Model

يُستخدم النموذج canonical `niam_verification_records` الموجود مسبقاً [3]، ويحفظ فقط:

```text
Verification ID
Account/Identity reference
Type and method
Provider
Status
Assurance level
Requested/started/completed/expiry/revocation timestamps
Provider reference
Failure reason code
Verification session ID
Professional reference/type when applicable
Minimal verified attributes and purpose
Audit linkage through canonical audit events
```

بعد نجاح contact OTP وقبل إتمام account creation، ينشئ approval flow سجل contact مرتبطاً بالحساب والهوية، مع `assurance_level=L1` و`verified_by=account_request_otp`. لا تُخزن صورة وثيقة، raw provider payload، OTP، token hash في serializer، أو biometric template.

## 7. Provider Boundary

يبقى `IdentityVerificationProvider` هو الحد الرسمي الذي يجب أن يلتزم به أي adapter لاحق. تشمل العمليات `start_verification`, `check_status`, `complete_verification`, `cancel_verification`, و`revoke_verification`. ويظل `NotConnectedProvider` يعيد `not_connected` أو `failed` و`L0` ولا يمكنه ادعاء success. هذا يمنع fake verification إلى أن تزود الجهة المالكة للهوية sandbox وcredentials وmTLS/OAuth وcallback contract.

لم يُنشأ adapter حكومي وهمي، ولم تُفعّل أي credentials أو feature flag. كما لم يُخلط WebAuthn مع National Identity؛ WebAuthn يثبت possession of a registered authenticator ضمن MFA وليس صحة الهوية الوطنية.

## 8. API Contract and Frontend

لم تُنشأ مسارات REST عامة جديدة بأسماء افتراضية. استُخدمت العقود الفعلية الحالية: `/auth/verification/request`, `/auth/verification/confirm`، ومسارات Account Request في `/niam/account-requests/*`. لا تُقبل identity أو assurance من العميل كسلطة نهائية.

أُكملت واجهة `RegisterPage` لتعرض Account Request وEnter Code وResend وPending Approval وActivation، وتعرض كذلك الحالات التالية دون كشف معلومات أمنية:

| الحالة | السلوك |
|---|---|
| Verification pending | يعرض انتظار المزود دون كشف وجود حساب إضافي. |
| Failed/Expired | يعرض رسالة عامة وخيار بدء طلب جديد. |
| Locked | يمنع التخمين ويعرض إيقافاً مؤقتاً دون إظهار counters حساسة. |
| Provider unavailable | يوضح أن الحساب لم يُنشأ وأنه لا توجد صلاحية ممنوحة. |
| Pending review/approval | يوضح أن التفعيل وتسجيل الدخول غير متاحين قبل القرار الرسمي. |
| Verified/activation | يسمح فقط بمسار activation token الرسمي بعد approval وidentity gate. |

لا تستخدم الواجهة Mock Verification في live mode ولا Legacy fallback لتجاوز NIAM.

## 9. Models and Migration

تم تعديل `VerificationRecordStatus` و`VerificationStatus` فقط من خلال قيم string متوافقة، دون تغيير جدول السجل canonical. أُضيفت إلى `AccountCreationRequest` حقول `verification_attempts`, `verification_locked_at`, و`verification_failure_reason_code`.

أُنشئت migration صغيرة قابلة للعكس [4]، revision `20260815_0024`، فوق `20260815_0023`. تم اختبار:

```text
upgrade 0024 → downgrade 0023 → upgrade 0024
```

على SQLite مؤقتة فقط، مع بقاء Alembic على رأس واحد هو `20260815_0024`.

## 10. Audit Events

يسجل المسار أحداثاً واضحة مثل:

```text
account_request_verification_started
account_request_verification_resent
account_request_verification_failed
account_request_verification_locked
account_request_verification_passed
account_request_pending_approval
account_request_approved
verification_provider_failed
```

تتضمن الأحداث actor/target/decision/reason/correlation عند توفرها، ولا تتضمن OTP أو password أو token أو secret أو raw identity document أو biometric data. القفل الدائم يكتب timestamp وreason code في الطلب، مع بقاء صلاحية فك القفل ضمن مسار governance/manual review وليس من Frontend العام.

## 11. Tests and Validation

| البوابة | النتيجة |
|---|---:|
| Backend non-integration suite | **2627 passed**, 41 integration tests لم تدخل هذا التشغيل. |
| Backend integration suite على SQLite مهاجرة مؤقتة | **40 passed، 1 skipped**؛ التخطي متعلق باعتماد clinical gateway غير المتصل. |
| Command 03 targeted verification/security tests | **33 passed**. |
| Frontend Vitest | **50 passed**. |
| Frontend typecheck | **ناجح**. |
| Frontend production build/PWA | **ناجح**. |
| Ruff على المسارات المعدلة | **ناجح**. |
| Python compileall | **ناجح**. |
| Migration 0024 upgrade/downgrade/upgrade | **ناجح** على SQLite المؤقتة. |
| Alembic head | **رأس واحد: 20260815_0024**. |
| `git diff --check` | **ناجح قبل commit**. |

## 12. Cross-platform Status

| المنصة | حالة Command 03 |
|---|---|
| Web/PWA | `IMPLEMENTED` لحالات Contact Verification وProvider Failure وLocked/Recovery ضمن RegisterPage، مع typecheck/test/build. |
| Backend | `IMPLEMENTED/PARTIAL`: state machine وOTP hardening وcanonical contact evidence موجودة؛ official provider غير متصل. |
| Android | `UNVERIFIED`؛ لا يوجد Android SDK في البيئة لتشغيل compileDebugKotlin. |
| Flutter Desktop | `UNVERIFIED`؛ Flutter SDK غير متاح محلياً. |
| iOS | `NOT_BUILT/UNVERIFIED`؛ Xcode غير متاح. |

## 13. Production Verification

تمت المراجعة من المصدر فقط. لم يتم التحقق live من providers أو secrets أو feature flags أو database state أو deployment commit في production، لذلك تصنف هذه البنود `UNVERIFIED`. لم يتم تعديل production أو تطبيق migration عليها أو تفعيل public registration أو government integration.

## 14. Remaining Gaps and Provider Dependencies

الفجوة الأساسية هي adapter الرسمي للهوية الحكومية. يلزم توفير sandbox موثق، client authentication، mTLS أو OAuth، callbacks موقعة، nonce/event replay protection، mapping للحالات، retention policy، incident runbook، وموافقة قانونية/أمنية قبل كتابة `identity_verified` أو منح `L2`.

كما أن professional registry وorganization registry غير موصولين، ولا توجد routes مستقلة لعرض VerificationRecord status للمستخدم أو governance reviewer beyond the current account request lifecycle. يمكن إضافة ذلك في Command لاحق بعد اعتماد عقد versioned، لكن لا ينبغي اختراع endpoint أو provider قبل توفر مالك البيانات والعقد.

يلزم كذلك تشغيل Android وFlutter CI، واختبار Redis متعدد العمال، ومراجعة WebAuthn RP ID/Origin لكل بيئة قبل production. لا تُعتبر هذه البنود ناجحة من مجرد وجود code أو UI.

## 15. Human Approval Required

يلزم اعتماد مكتوب من مالك الهوية الوطنية والخصوصية والأمن ومالك المنصة قبل: توصيل provider رسمي، إضافة credentials أو mTLS، تطبيق migration على staging، تفعيل callback، إعطاء governance permission، أو تشغيل canary. لا يجوز تجاوز `NotConnectedProvider` أو تحويل `VERIFICATION_PARTIAL` إلى `VERIFICATION_COMPLETE` يدوياً.

## 16. Production Actions NOT Performed

لم يتم تنفيذ production deployment، ولا production database migration، ولا public registration activation، ولا government registry/OCR/NFC/biometric activation، ولا push، ولا merge، ولا PR جديد، ولا تغيير حماية الفروع. لا تبدأ Command 04 تلقائياً.

## References

[1]: ./COMMAND03_VERIFICATION_INVENTORY_AR.md "Command 03 verification inventory"
[2]: ../../backend/tests/identity/test_verification_hardening_command03.py "Command 03 OTP hardening tests"
[3]: ../../backend/app/identity/models/verification_record.py "Canonical verification evidence model"
[4]: ../../backend/migrations/versions/20260815_0024_verification_hardening.py "Reversible verification hardening migration"
[5]: ../../backend/app/identity/services/verification_record_service.py "Verification state machine and provider result mapping"
[6]: ../../backend/app/identity/services/verification_service.py "Provider boundary and assurance policy"
[7]: ../../backend/app/routes/verification.py "Legacy contact verification routes"
[8]: ../../frontend-v3/src/pages/auth/RegisterPage.tsx "Verification and recovery UI"
