# GULA Command 05 — Account Recovery & Security Lifecycle

## القرار

> **RECOVERY_PARTIAL / SAFE_STOP**

تم تنفيذ إصلاح أمني قابل للإثبات في إدارة الجلسات، لكن لا يجوز إعلان اكتمال دورة Recovery لأن مسارات استرداد الحساب وIdentity Assurance وMFA Recovery وPasskey Recovery وContact Change الآمنة ليست مكتملة بعقد server-authoritative قابل للاختبار end-to-end. لم يتم إنشاء bypass أو تفعيل استرداد تلقائي ضعيف.

## Recovery Inventory

| المجال | الحالة | الدليل أو الملاحظة |
|---|---|---|
| Account creation request | PARTIAL | يوجد `/account-requests/` review-gated، لكنه إنشاء طلب حساب وليس Forgot Access/Recovery. |
| Password/Forgot Access | MISSING | لم يثبت وجود مسار استرداد كلمة مرور مكتمل enumeration-resistant مع verification وexpiry. |
| Session listing | PARTIAL → HARDENED | كان يقبل `account_id` من العميل؛ أصبح يتحقق من `NiamActor` ويمنع cross-account scope. |
| Session termination | PARTIAL → HARDENED | أصبح يمنع إبطال session لا تنتمي للحساب المصادق عليه قبل تنفيذ mutation. |
| Terminate all sessions | PARTIAL → HARDENED | أصبح يرفض account scope المخالف server-side. |
| Refresh token rotation | COMPLETE بالنسبة للمنطق المثبت | الاختبارات الحالية تثبت rotation وblacklist ورفض replay. |
| Device loss/revocation | UNVERIFIED/PARTIAL | توجد مكونات أجهزة، لكن لم يثبت مسار دورة Lost Device → Verify → Revoke Device → Revoke Sessions → Re-authenticate كاملاً. |
| MFA recovery | UNVERIFIED | توجد مكونات adaptive/MFA، لكن لم يثبت Recovery Codes أو reset/re-enrollment بمستوى assurance مناسب. |
| Passkey/WebAuthn recovery | UNVERIFIED/PARTIAL | لا يجوز ادعاء دعم recovery الكامل دون proof end-to-end. |
| Account lock/unlock | PARTIAL | توجد حالات lock وبعض hardening، لكن لا توجد دورة Recovery/Manual Review كاملة مثبتة. |
| Security alerts | PARTIAL/UNVERIFIED | توجد بنية notifications/security، لكن تغطية Recovery Started/Completed وMFA/Passkey/Contact/Session events غير مثبتة كاملة. |
| Audit | PARTIAL | توجد خدمات canonical/security audit، لكن Recovery event set الكامل غير مكتمل. |

## Required Recovery State Machine

```text
REQUESTED → VERIFYING → VERIFIED → APPROVED → RECOVERED
                 │           │          │
                 ├→ FAILED   ├→ REJECTED ├→ SUSPICIOUS
                 ├→ EXPIRED  └→ PENDING_REVIEW
                 ├→ LOCKED
                 └→ CANCELLED
```

كل انتقال يجب أن يحمل `actor`, `reason_code`, `scope`, `request_id`, `correlation_id`، وأن يكون idempotent ومقيداً زمنياً. لم يتم تفعيل هذه الآلة ناقصة الإثبات في Production.

## الإصلاح المنفذ

تم تأمين `backend/app/identity/api/sessions.py` باستخدام `get_current_niam_actor`. أصبح الخادم يستخرج الحساب والجلسة من access token وsession record، ويرفض:

- listing لحساب يختلف عن الحساب المصادق عليه؛
- termination لجلسة تنتمي إلى حساب آخر؛
- terminate-all لحساب يقدمه العميل ولا يطابق actor server-side.

أضيفت اختبارات regression تثبت أن كل cross-account deny يحدث قبل أي mutation.

## Security Controls Not Implemented Because Assurance Was Missing

لم يتم إنشاء Forgot Access أو MFA reset أو Passkey recovery أو Contact Change تلقائي لأن وسائل verification والتسليم الآمن وmanual review غير مثبتة في Commands 01–04. إضافة مسار يرسل OTP أو يغير contact أو ينشئ session جديدة دون assurance كافٍ ستخفض مستوى الأمان، ولذلك تم تطبيق **SAFE_STOP** بدلاً من bypass.

## Tests

| الاختبار | النتيجة |
|---|---|
| Session scope hardening | 3 ناجحة |
| Existing auth/session security | 5 ناجحة |
| Workspace actor hardening | 5 ناجحة |
| Security audit phase tests | 10 ناجحة |
| Global rate limit | 2 ناجحة |
| Resilience smoke | 22 ناجحة |
| Python compileall | ناجح |
| git diff --check | ناجح |

## Production Safety

لم يتم نشر Production، ولم تعدل قاعدة بيانات Production أو secrets أو feature flags أو public registration. لم يتم تغيير أي مسار Recovery غير مثبت، ولم يبدأ Command 06.

## Human Approval Required

قبل استكمال Recovery يجب اعتماد تصميم بشري/تشغيلي يحدد وسائل Identity Assurance الفعلية، قنوات إرسال verification، فترة الصلاحية، manual review، security notification، جلسات الإبطال، وسياسة MFA/Passkey. بعدها يمكن إنشاء عقد versioned وmigration واختبارات deny/mutation وواجهة حقيقية دون Mock Recovery.
