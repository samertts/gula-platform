# ربط موفر التحقق الرسمي للهوية مع GULA/NIAM

## القرار التنفيذي

يجب أن يتم الربط على مرحلتين: **اعتماد وتنفيذ adapter رسمي في staging**، ثم تفعيل تدريجي بعد اجتياز اختبارات الهوية والعزل والأمان. لا يجوز اعتبار OTP للبريد أو الهاتف إثبات هوية وطنية؛ فهو يثبت وسيلة الاتصال فقط. يبقى `NotConnectedProvider` هو السلوك الآمن إلى أن يصبح الموفر الرسمي متصلاً وقابلاً للإثبات.

## 1. المتطلبات الرسمية قبل البرمجة

يجب أولاً الحصول على موافقة الجهة المالكة للهوية الوطنية والوزارة وفريق الأمن، وتوثيق غرض المعالجة والبيانات المسموح تبادلها ومدة الاحتفاظ بها. يلزم الحصول على مواصفات sandbox، عناوين الإنتاج، طريقة المصادقة، الشهادات، scopes، آلية callback/webhook، أكواد الأخطاء، اتفاقية مستوى الخدمة، وإجراء إلغاء الشهادة.

لا تُستخدم بيانات مواطنين حقيقية في sandbox. يبدأ الاختبار بمعرفات اصطناعية أو حالات اختبار رسمية من الموفر، مع فصل كامل بين حسابات وأسرار وقاعدة بيانات وRedis الخاصة بـstaging وتلك الخاصة بالإنتاج.

## 2. تنفيذ adapter وفق العقد الموجود

يوجد في المشروع عقد `IdentityVerificationProvider` يعرّف العمليات `start_verification` و`check_status` و`complete_verification` و`cancel_verification` و`revoke_verification`. يجب إنشاء adapter جديد، مثلاً `OfficialIdentityProviderAdapter`، ولا ينبغي استدعاء HTTP الخاص بالموفر مباشرة من route أو من واجهة الويب.

| عقد GULA | سلوك adapter المطلوب |
|---|---|
| `start_verification` | ينشئ جلسة لدى الموفر، ويربطها بـ`account_id` و`identity_id` وnonce داخلي، ويعيد provider session/reference دون كشف PII. |
| `check_status` | يستعلم عن الجلسة باستخدام provider reference، ويتحقق من التوقيع/الشهادة، ويحول الحالة إلى `pending`, `verified`, `failed`, `expired` أو `revoked`. |
| `complete_verification` | يقبل callback أو evidence موثقاً فقط بعد التحقق من state وnonce وربط الجلسة بالطلب الصحيح. |
| `cancel_verification` | يلغي الجلسة عند انتهاء الطلب أو إلغاء المستخدم. |
| `revoke_verification` | يسجل سحب الثقة ويعيد الحساب إلى حالة لا تسمح بالتفعيل إذا كانت السياسة تتطلب ذلك. |

يُسجل adapter في factory/registry يعتمد على إعداد بيئي صريح مثل `OFFICIAL_IDENTITY_PROVIDER=...`. إذا غاب الإعداد أو فشل الاتصال، يجب أن يعيد `connected=False` و`VerificationStatus.not_connected`، لا نجاحاً اصطناعياً.

## 3. المصادقة والنقل الآمن

يُفضّل استخدام mTLS أو OAuth 2.0 client credentials وفق متطلبات الموفر، مع تخزين client secret والمفتاح الخاص وشهادة العميل في Secret Manager لا في Git أو `.env` المرفوع. يجب تقييد TLS والتحقق من hostname والشهادة، ووضع timeout قصير، وretry محدود للطلبات الآمنة فقط، وcircuit breaker عند تعطل الموفر.

يجب أن تكون callbacks محمية بـmTLS أو توقيع HMAC/ JWS مع منع replay عبر nonce وtimestamp وprovider event ID. لا يُقبل callback بلا ربط بجلسة داخلية صالحة، ولا يُقبل event أقدم من نافذة السماح أو مكرر.

## 4. ربط النتيجة بدورة الحساب

المسار الصحيح هو:

```text
Account Request
→ Contact Verification (OTP اختياري/مطلوب حسب السياسة)
→ Official Identity Verification
→ Review
→ Approval
→ Account Creation/Approved
→ Activation Token
→ Active
```

يجب الفصل بين `email_verified` أو `phone_verified` وبين `identity_verified`. عند نجاح الموفر الرسمي فقط تُحفظ `provider_reference` و`verification_method=official_identity` و`assurance=L2` أو المستوى الذي تعتمده الجهة. تُحفظ أقل مجموعة من السمات اللازمة، وتُشفّر المراجع الحساسة، ولا تُخزن صورة الهوية أو raw payload إلا إذا كان هناك أساس قانوني وسياسة احتفاظ معتمدة.

بعد نجاح الهوية، يستطيع المسار الانتقال إلى `verified` أو `pending_approval` وفق سياسة الحساب. لا يمنح نجاح التحقق Role أو Membership أو Workspace؛ هذه تبقى من اختصاص Authorization وgovernance approval. ولا يصدر activation token قبل تحقق الهوية والاعتماد.

## 5. الإعدادات المقترحة في staging

يجب توفير إعدادات منفصلة، مثل:

```text
OFFICIAL_IDENTITY_PROVIDER=official_registry
OFFICIAL_IDENTITY_BASE_URL=https://sandbox.provider.example
OFFICIAL_IDENTITY_CLIENT_ID=<secret-manager-reference>
OFFICIAL_IDENTITY_CLIENT_SECRET=<secret-manager-reference>
OFFICIAL_IDENTITY_MTLS_CERT=<secret-manager-reference>
OFFICIAL_IDENTITY_MTLS_KEY=<secret-manager-reference>
OFFICIAL_IDENTITY_CALLBACK_AUDIENCE=gula-staging
OFFICIAL_IDENTITY_TIMEOUT_SECONDS=10
OFFICIAL_IDENTITY_ENABLED=false
```

الأسماء النهائية تعتمد على مواصفات الموفر. المهم أن تكون `OFFICIAL_IDENTITY_ENABLED=false` هي القيمة الافتراضية، وأن يفشل النظام مغلقاً عند غياب الشهادات أو عدم تطابق البيئة.

## 6. الاختبارات الإلزامية قبل التفعيل

| الفئة | حالات الاختبار |
|---|---|
| النجاح | هوية اختبار صحيحة، callback صحيح، انتقال إلى المستوى المطلوب، ثم approval وactivation. |
| الرفض | هوية غير مطابقة، provider rejection، إلغاء، expiry، revoked reference، وبيانات ناقصة. |
| مقاومة replay | callback مكرر، nonce مكرر، event ID مكرر، timestamp قديم، وtoken معاد الاستخدام. |
| العزل | طلب من tenant آخر، workspace خاطئ، account غير مرتبط بالجلسة، وcallback مربوط بطلب مختلف. |
| الاعتمادية | timeout، 5xx، rate limit، circuit breaker، retry غير آمن، وانقطاع Redis/provider. |
| الخصوصية | عدم ظهور PII أو raw payload أو access token أو provider secret في logs/audit/traces. |
| دورة الحساب | منع `ACTIVE` قبل الهوية والاعتماد، ومنع bypass من frontend، واحترام suspended/locked/deactivated. |

يجب أن تمر اختبارات Backend وFrontend، ثم Android/Flutter CI، ثم DAST سلبي وPentest مرخص على staging. لا تُعتبر نتيجة provider ناجحة بمجرد أن endpoint أعاد HTTP 200؛ يجب إثبات توقيع الاستجابة والحالة والمرجع.

## 7. خطة التفعيل التدريجي

يبدأ الفريق بـfeature flag مغلق في production، ثم sandbox staging ببيانات اصطناعية، ثم اختبار قبول أمني وتشغيلي، ثم canary محدود بمستخدمين مخولين وبلا صلاحية تسجيل عام. بعد مراجعة الأمن والخصوصية والجهة المالكة، يُفعّل provider لفئة محددة، وتراقب معدلات النجاح والفشل والـlatency والـreplay والـfallback.

إذا فشل provider أو لم يمكن التحقق من النتيجة، تبقى الحالة `pending` أو `not_connected` ولا يتحول الحساب إلى `active`. يجب وجود runbook لتعطيل feature flag وإلغاء الشهادات وسحب جلسات التحقق عند incident.

## 8. بوابة الموافقة النهائية

قبل production يلزم اعتماد مكتوب من مالك الهوية والـDPO/الخصوصية وفريق الأمن ومالك المنصة، مع مراجعة migration إن وجدت، وفحص secrets، وإثبات عزل قاعدة بيانات staging، وتجربة rollback. حتى اكتمال ذلك، يبقى قرار GULA هو `SAFE_STOP` ولا يُفعّل التسجيل العام أو National ID أو OCR/NFC/biometrics.

## مراجع المستودع

[1]: ../../backend/app/identity/services/verification_service.py "IdentityVerificationProvider وVerificationPolicy"
[2]: ../../backend/app/identity/services/account_request_service.py "Account Request lifecycle وactivation gate"
[3]: ../../backend/app/identity/api/account_requests.py "واجهات verification وapproval وactivation"
[4]: ../../security-audit/20260815/P0_IDENTITY_ACCOUNT_LIFECYCLE_COMMAND02_AR.md "تقرير Command 02 والفجوات الحالية"
