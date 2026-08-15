# Command 03 — جرد طبقة التحقق الأولي

## قاعدة التصنيف

وجود نموذج أو واجهة أو Protocol لا يثبت أن التكامل يعمل. التصنيف هنا مبني على مسارات التشغيل والاختبارات والـprovider wiring الموجود في المستودع.

| القدرة | التصنيف الحالي | الدليل/الملاحظة |
|---|---|---|
| Email verification | `PARTIAL` | `/auth/verification` يولد OTP digest ويستخدم NotificationService، لكنه خاص بنموذج `User` legacy وليس VerificationRecord/NIAM بشكل كامل. |
| Phone/SMS OTP | `PARTIAL` | Account Request يرسل OTP عبر NotificationService ويضع digest في cache، مع TTL ومحاولات محدودة؛ لا يوجد resend throttling مخصص أو VerificationRecord wiring. |
| Canonical contact verification | `PARTIAL` | AccountRequestService يثبت channel/provider في الطلب، لكنه لا ينشئ `niam_verification_records` canonical. |
| Official identity | `NOT_CONFIGURED` | يوجد `IdentityVerificationProvider` و`NotConnectedProvider` وpolicy L2، ولا يوجد adapter رسمي موصول أو route canonical. |
| Professional verification | `NOT_CONFIGURED` | `VerificationRecord` و`ProfessionalType` موجودان، لكن لا يوجد registry adapter أو endpoint lifecycle موصول. |
| Organization verification | `NOT_CONFIGURED` | نوع record موجود، لكن لا توجد خدمة/provider/approval evidence flow مستقلة موصولة. |
| Government registry | `NOT_CONFIGURED` | لا توجد credentials أو endpoint أو provider مثبت في البيئة؛ يجب إبقاؤه dependency. |
| OCR | `BLOCKED` | لا يُسمح بتفعيله أو اعتبار أي implementation نجاحاً دون اعتماد رسمي. |
| NFC | `BLOCKED` | لا يُسمح بتفعيله أو ربطه بالهوية الوطنية. |
| Biometrics | `BLOCKED` | لا توجد موافقة قانونية/تصميم تخزين templates؛ لا يُفعّل. |
| Passkey/WebAuthn | `IMPLEMENTED` للمصادقة/MFA فقط | MFA routes وMFAService يدعمان التسجيل والمصادقة؛ لا يرفعان `identity_verified` ولا يمثلان Government Identity. |
| Device biometrics | `UNVERIFIED` | لا يوجد مسار موصول في Backend يربطه بهوية وطنية؛ لا يُعامل كـIdentity Assurance. |

## العقود الحالية

يوجد `VerificationRecord` canonical يحفظ الحد الأدنى من evidence: النوع، الطريقة، provider، الحالة، assurance، timestamps، provider reference، failure code، session ID، والسمات المصرح بها. كما توجد `VerificationRecordService` و`VerificationPolicy` و`AssuranceEngine` مع اختبارات تمنع provider غير المتصل من ادعاء النجاح أو assurance.

الفجوة الأساسية هي أن OTP في AccountRequestService و`/auth/verification` يعملان كمسارين منفصلين ولا يكتبان إلى VerificationRecord canonical. لذلك لا يصح تصنيف طبقة التحقق الحالية على أنها `VERIFICATION_COMPLETE`.

## مراجع الأدلة

[1]: ../../backend/app/routes/verification.py "Legacy email/phone verification routes"
[2]: ../../backend/app/identity/services/account_request_service.py "NIAM account request OTP flow"
[3]: ../../backend/app/identity/models/verification_record.py "Canonical verification evidence model"
[4]: ../../backend/app/identity/services/verification_record_service.py "Canonical verification record state machine"
[5]: ../../backend/app/identity/services/verification_service.py "Provider boundary and assurance policy"
[6]: ../../backend/tests/identity/test_verification_hardening_phase3.py "Assurance and NotConnectedProvider tests"
[7]: ../../backend/app/routes/mfa.py "MFA/WebAuthn authentication routes"
