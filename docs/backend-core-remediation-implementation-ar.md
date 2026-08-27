# تنفيذ Backend Core Remediation

## النطاق

تُنفذ هذه الوثيقة أول موجة Backend Remediation آمنة بعد اكتمال أساس `frontend-v3` وملفات Frontend Master Specification. الهدف هو جعل الخادم يساعد المطور على اكتشاف فجوات العقد والحالات والأدلة، مع بناء Test Backend اصطناعي يثبت المسار الأساسي داخل الاختبارات فقط. لا تُنشئ هذه الموجة بيانات إنتاجية ولا تُجري تكاملاً خارجياً ولا ترفع أي Domain إلى Production Ready.

## ما أُضيف

أضيف `backend/app/contracts/clinical_core.py` كسجل مركزي typed لعقود Appointment وSession وDevice وPatient Access وConsent وAccess History وDelegation وTask وEncounter وClinical Note وLab Order وSpecimen وResult وCritical Result وNotification. يتضمن السجل الحالات والانتقالات المسموحة ومتطلبات الكتابة الحساسة مثل authorization وobject-level authorization وtenant isolation وaudit وidempotency وconcurrency وrate limits وerror contract.

أضيف `backend/app/contracts/engineering_intelligence.py` لتوليد تقرير مبني على Evidence فعلية. يعرض التقرير العقد والـreadiness والنسبة المحسوبة وقائمة الأدلة الموجودة والمفقودة ورسالة سبب الفجوة والإصلاح المقترح. لا يستخدم هذا المحرك كلمة `READY_FOR_PRODUCTION` إلا عند اكتمال كل الأدلة المطلوبة للعقد، ولا يخلط بين وجود TypeScript/Pydantic type وبين وجود API أو migration أو اختبار أمني.

أضيف `backend/tests/fixtures/synthetic_core_backend.py` كـTest-only backend داخل الذاكرة. يثبت Golden Path اصطناعياً:

```text
Citizen
  → Appointment + idempotency + no double booking
  → Doctor confirmation
  → Citizen check-in
  → Encounter
  → Clinical Note signed
  → Lab Order
  → Specimen collection/receipt/processing
  → Senior lab validation
  → Result release
  → Citizen read
  → Consent share
  → Recipient read
  → Revoke
  → Recipient denied
  → Audit events
```

هذا fixture ليس خدمة API، ولا يقرأ قاعدة البيانات، ولا يرسل إشعارات، ولا يصل إلى production أو staging. الغرض منه هو تثبيت قواعد المسار والاختبارات قبل إنشاء migrations وservices وroutes الفعلية.

## الأدلة الحالية

| المجال | الحالة الحالية | الدليل |
|---|---|---|
| Contract Registry | `BUILDING` | typed definitions واختبارات الانتقالات |
| Engineering Intelligence | `READY_FOR_REVIEW` كأداة تطوير | تقرير الأدلة واختبار النسبة والفجوات |
| Synthetic Core Journey | `TESTING` | 3 اختبارات Golden E2E اصطناعية |
| Appointment production API | غير مكتمل | توجد خدمة scheduling قديمة، لكنها admin-oriented وraw dict ولا تثبت core workspace scope |
| Encounter/Lab/Result production API | غير مكتمل | لا توجد بعد service/routes/migrations مترابطة ومثبتة للمسار الجديد |
| Audit production integration | غير مكتمل | fixture يسجل audit في الذاكرة؛ لم يُربط بعد بكل mutation خادمية للمسار الجديد |
| Remote CI/Staging/Rollback | غير مثبت | يحتاج بيئة وصلاحيات وتشغيلاً بعيداً قابلاً لإعادة الإنتاج |

## ضوابط لا يجوز تجاوزها

وجود عقد typed أو fixture ناجح لا يمنح المستخدم دوراً أو Workspace أو Patient Access أو Consent. كل API كتابة مستقبلية يجب أن تفحص actor والسياق والـtenant والمنشأة والقسم والعلاقة والغرض، وتسجل قرار السماح أو الرفض دون وضع بيانات سرية غير لازمة في السجل.

يجب أن ترفض الخدمة الانتقال غير المسموح، والتعديل على نسخة قديمة، وإعادة استخدام Idempotency-Key مع payload مختلف، ومحاولة القراءة خارج المؤسسة أو العلاقة. يجب أن يكون conflict صريحاً وقابلاً للمراجعة، لا overwrite صامتاً.

## الخطوة التالية

الخطوة التالية ليست إضافة صفحات جديدة. الأولوية هي اختيار عقد واحد للإنتاج، والأفضل Appointment أو Identity/Session، ثم تنفيذ دورة كاملة بالترتيب التالي: schema/migration، repository، domain service، authorization context، audit، idempotency، version/If-Match، typed API/error envelope، contract tests، security negatives، ثم ربط frontend بعد نجاح Synthetic Test Backend. لا تُفتح Pharmacy أو Imaging أو Hospital أو Emergency أو Insurance قبل ثبات هذا المسار.

## النتيجة

هذه الموجة نقلت المشروع من سجل فجوات frontend فقط إلى أساس Backend developer-assistance قابل للاختبار. لكنها لا تثبت بعد رحلة سريرية إنتاجية، ولا تبرر إعلان `GOLDEN PATH PASSED` أو `PRODUCTION READY`.
