# مواصفة حدود حساب المواطن وقراءة الأجهزة

## الحالة والقرار

هذه الوثيقة **مواصفة وتحضير فقط**، وليست تفويضًا لتفعيل تسجيل المواطنين أو الهوية الوطنية أو OCR أو NFC أو الكاميرا أو QR في بيئة التشغيل.

```text
CITIZEN_ACCOUNT = READY_FOR_GOVERNED_IMPLEMENTATION
CITIZEN_ACCOUNT_ACTIVATION = OFF
CAMERA_CAPTURE = OFF
QR_READER = OFF
OCR_READER = OFF
NFC_READER = OFF
IDENTITY_PROOFING = OFF
```

لا يبدأ التنفيذ التشغيلي لهذه القدرات قبل إغلاق P0–P3، وإكمال P4 رسميًا، والحصول على مراجعة بشرية صريحة. نجاح الاختبارات وحده لا يساوي موافقة تشغيلية.

## مبدأ الهوية

> قراءة معلومة من كاميرا أو QR أو OCR أو NFC ليست إثباتًا للهوية، ولا تنشئ Account أو Person أو Identity أو Citizen record، ولا تمنح صلاحية.

كل قراءة تنتج **Candidate Data** غير موثوق. التحويل من Candidate Data إلى Verified Identity يحتاج إلى سياسة تحقق مستقلة، مصدر رسمي موثق عند الحاجة، قرار خادمي، مراجعة تدقيقية، ومطابقة تعارضات. لا يجوز قبول اسم الجهة أو نوع المستند أو محتوى QR الذي يرسله المستخدم كسلطة أو permission.

## مسار حساب المواطن المقترح

```text
LOCAL_DRAFT
  → SUBMITTED_PENDING_REVIEW
  → NEEDS_REVIEW
  → APPROVED_BY_AUTHORIZED_REVIEWER
  → ACCOUNT_CREATED
  → ACTIVE_AFTER_SEPARATE_ACTIVATION_POLICY
```

الحالة العامة الحالية هي `SUBMITTED_PENDING_REVIEW` فقط. لا يوجد في هذا النطاق endpoint عام للموافقة أو إنشاء الحساب أو تفعيل citizen workspace أو منح role أو permission. لا يجوز للعميل إرسال `status`, `account_id`, `actor_id`, `verification_level`, `membership_status` أو أي قرار authoritative.

## عقد طلب المواطن

يُسمح في مرحلة intake بجمع أقل قدر لازم من بيانات التواصل، مثل البريد الإلكتروني أو الهاتف واسم العرض، مع `Idempotency-Key`. لا تُطلب صورة هوية أو رقم وطني أو بصمة أو NFC payload داخل المحادثة أو عبر مسار غير معتمد.

| الحقل | النوع | القاعدة |
|---|---|---|
| `email` | اختياري | تطبيع وتحقق، ثم تشفير؛ لا يستخدم كهوية موثوقة وحده |
| `phone` | اختياري | تطبيع وتحقق، ثم تشفير؛ لا يستخدم كهوية موثوقة وحده |
| `display_name` | اختياري | Candidate label فقط |
| `requested_account_type` | ثابت | `human` أو `citizen_request` بعد اعتماد العقد؛ لا يفعّل صلاحيات |
| `Idempotency-Key` | header مطلوب | يمنع side effects المكررة |
| `source` | server-generated | لا يقبله العميل كقرار ثقة |
| `status` | server-generated | يبدأ `PENDING_REVIEW` فقط |

## الكاميرا

تُستخدم الكاميرا فقط بعد موافقة صريحة وfeature flag خادمية. المعالجة الافتراضية تكون داخل الجهاز وبذاكرة مؤقتة؛ لا تُحفظ الصورة في gallery أو cache دائم، ولا تُرفع إلى الخادم إلا إذا كان هناك غرض معتمد وعقد API وتشفير وسياسة حذف واختبارات تسريب.

يجب أن يرفض التطبيق لقطات الشاشة أو الصور غير الواضحة عند الحاجة، ويعرض للمستخدم ما تم اكتشافه قبل الإرسال. لا يجوز اعتبار نجاح التقاط الصورة تحققًا من المستند أو الشخص.

## QR Code

قارئ QR يعالج payload محليًا مع allowlist للإصدارات والحقول. يجب رفض deep links غير المعتمدة، URLs غير المسموحة، payloads التنفيذية، والبيانات التي تحتوي على secrets أو tokens غير مخصصة لهذا الغرض. لا تُنفذ أي قيمة مقروءة تلقائيًا، ولا تُستخدم لرفع الصلاحيات.

إذا كان QR خاصًا بـGULA، فيجب أن يكون versioned وموقعًا خادميًا، مع expiry وnonce وpurpose وaudience وrevocation. لا يكفي وجود citizen ID داخل QR لربط الحساب تلقائيًا.

## OCR

OCR ينتج حقولًا مرشحة مع confidence وsource وtimestamp، وليس هوية موثوقة. يجب:

1. إبقاء الصورة والنتيجة الخام في الذاكرة المؤقتة فقط افتراضيًا.
2. تنظيف النص من control characters وحقن المحتوى.
3. عرض candidate fields للمستخدم قبل الإرسال.
4. رفض المطابقة التلقائية عند التعارض أو confidence المنخفض.
5. تسجيل hash للحدث عند الحاجة بدل تسجيل الصورة أو النص الكامل.
6. إبقاء أي تكامل حكومي أو مهني في حالة `READY_FOR_OFFICIAL_INTEGRATION` ما لم يوجد مصدر رسمي وعقد موثق.

لا يجوز استخدام OCR لإثبات رقم وطني أو مستند عراقي أو جنسية دون سياسة ومصدر تحقق معتمدين.

## NFC

يُسمح مستقبلًا بقراءة NDEF أو secure-element data فقط عبر adapter معتمد ومحدد الغرض. لا يُخزن UID أو APDU أو payload الخام افتراضيًا. لا تُستخدم NFC وحدها لإنشاء identity أو ربط person أو منح access.

يجب أن يتحقق adapter من hardware support وpermission وuser consent وtag type وread timeout وreplay resistance. أي قارئ لمستند وطني أو شريحة حكومية يحتاج مواصفات رسمية، مصدر تحقق، اختبار أمني، وسياسة قانونية؛ لا يجوز اختراع protocol أو الادعاء بدعم جهة حكومية.

## أي تقنية أخرى لقراءة المعلومات

أي تقنية مستقبلية، مثل barcode أو Bluetooth reader أو document scanner أو secure camera pipeline، يجب أن تدخل عبر interface موحد:

```text
ReaderAdapter
  → CaptureResult(candidate_data, provenance, confidence, expires_at)
  → ValidationPolicy
  → Server Review / Official Verification
  → IdentityLinkDecision
```

الـadapter لا يملك صلاحية إنشاء الحساب أو تغيير status أو membership أو role. والـclient لا يملك صلاحية تفعيل feature flag أو اعتماد النتيجة.

## حماية البيانات

يجب تشفير البيانات الحساسة في التخزين باستخدام مفاتيح deployment-managed، واستخدام blind indexes keyed-HMAC عند الحاجة للتكرار، وعدم تسجيل الصور أو OCR text أو NFC payload أو QR secrets أو authorization headers أو cookies. يجب تطبيق retention قصيرة ومحددة لكل artifact، مع حذف آمن، و`LEGAL_REVIEW_REQUIRED` لأي مدة غير موثقة.

يجب أن تكون responses غير قابلة لتعداد المستخدمين أو المواطنين. عند فشل key material أو adapter أو official verification يجب الفشل المغلق برسالة عامة دون stack trace أو تفاصيل configuration.

## Feature flags

الأسماء المقترحة، وجميعها **server-controlled وOFF افتراضيًا**:

| Flag | Default | من يملك التفعيل |
|---|---|---|
| `GULA_CITIZEN_ACCOUNT_REQUESTS` | `OFF` | server governance فقط |
| `GULA_CAMERA_CAPTURE` | `OFF` | server governance فقط |
| `GULA_QR_READER` | `OFF` | server governance فقط |
| `GULA_OCR_READER` | `OFF` | server governance فقط |
| `GULA_NFC_READER` | `OFF` | server governance فقط |
| `GULA_IDENTITY_PROOFING` | `OFF` | separate reviewed workflow |
| `GULA_OFFICIAL_VERIFICATION_ADAPTER` | `OFF` | official integration owner |

يجب ألا يستطيع browser أو mobile client إرسال flag لتفعيله، وألا تتغير قيمة flag دون audit وowner وscope وrollback.

## شروط الجاهزية قبل التنفيذ التشغيلي

| الشرط | الدليل المطلوب |
|---|---|
| P0–P3 closure | PRs reviewed/merged/deployed/verified، لا `REVIEW_REQUIRED` |
| P4 closure | كل mandatory rows في `P4_ACCEPTANCE_MATRIX.md` = `COMPLETE` |
| Citizen account model | فصل Account/Person/Identity/Citizen وserver-authoritative transitions |
| Official verification | مصدر رسمي وعقد موثق، أو بقاء adapter غير تشغيلي |
| Privacy | data inventory، minimization، retention، deletion، و`LEGAL_REVIEW_REQUIRED` حيث يلزم |
| Security | replay, spoofing, injection, enumeration, tenant isolation, rate limit, audit tests |
| Mobile parity | Android/iOS/Web/Desktop contract parity أو تصنيف صريح `NOT_BUILT` |
| Rollback | تعطيل flags وحذف artifacts دون كسر audit أو account integrity |
| Runtime | Vercel/backend/database/feature flag evidence على merge commit الصحيح |
| Human review | موافقة صريحة قبل تفعيل أي reader أو citizen activation |

## القرار الحالي

بسبب بقاء P4 غير مغلقة، ووجود PR #188 بحالة `REVIEW_REQUIRED` وVercel rate-limit، لا يتم الآن إضافة runtime paths للكamera أو QR أو OCR أو NFC، ولا يتم إنشاء حساب مواطن فعلي أو طلب مستند هوية. هذه الوثيقة تجهز العقد والحدود فقط حتى لا يتحول طلب القراءة إلى مسار هوية أو صلاحيات غير محكوم.
