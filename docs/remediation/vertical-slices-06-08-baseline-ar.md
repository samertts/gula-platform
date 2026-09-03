# Baseline وADR لشرائح GULA السريرية 06–08

**التاريخ:** 2026-08-28
**الفرع:** `feat/citizen-journey-20260827`
**آخر commit مرجعي قبل هذه الموجة:** `660a9eb8924e0da05fbdafa589a9515d5e61efea`
**نطاق الدليل:** بيانات اصطناعية محلية فقط؛ لا يمثل staging أو production.

## القرار المعماري

تم اعتماد حدود canonical additive فوق NIAM للكتابات السريرية الجديدة. تبقى نماذج ومسارات Pharmacy وRadiology وEHR القديمة خارج مسار الكتابة canonical، ولا يوجد dual-write أو تحويل صامت للبيانات. مالك الحقيقة في الوصفة والصرف هو `backend/app/clinical/pharmacy/`، ومالك الحقيقة في طلبات التصوير والدراسات والتقارير هو `backend/app/clinical/imaging/`. أما `Unified Clinical Record` في `backend/app/clinical/record/` فهو read model وتجميع محكوم، وليس قاعدة مرضى أو هوية أو تدقيق أو مشاركة جديدة.

> وجود package وmigration واختبارات محلية لا يساوي جاهزية إنتاجية. لا تزال حالة `golden_path_passed=false` و`production_ready=false` عمداً إلى أن تتوفر أدلة CI قابلة للقراءة وstaging وrollback وconcurrency production-like.

## خريطة الملكية ومنع التكرار

| المجال | المصدر canonical للكتابات الجديدة | المكونات القديمة التي بقيت معزولة | القرار والحد الأمني |
|---|---|---|---|
| Medication/Prescription | `clinical/pharmacy/models.py`, `service.py`, `routes.py` | `app/pharmacy/models.py` و`ehr/models/medication.py` | لا تُفتح legacy writes للرحلة الجديدة؛ الوصفة الموقعة غير قابلة للتعديل، والتعديل إصدار جديد مع `supersedes_id` وسبب وتدقيق. |
| Dispensing/Inventory | `CoreMedicationBatch`, `CoreMedicationStockLedger`, `CoreDispense` | legacy pharmacy dispensing/POS | الصرف محمي بقفل صف، دفتر append-only، منع batch منتهية أو محجورة، منع المخزون السالب وover-dispense، وفصل التحضير عن الإتمام. |
| Imaging | `clinical/imaging/` | `app/radiology/models.py` ومسارات radiology القديمة | لا DICOM binary في PostgreSQL، لا public image URL، ولا auto-match بالاسم؛ الاستلام metadata فقط عبر adapter contract اصطناعي وحالة quarantine عند عدم الصلاحية. |
| Sharing | `clinical/access/` القائم | أي public-token أو sharing legacy | `imaging_report` أعيد استخدامه داخل Access Grant القائم مع purpose/scope/expiry/revoke؛ لم يُنشأ sharing engine ثانٍ. |
| Unified Record | `clinical/record/service.py` فوق Encounter/Note/Lab/Pharmacy/Imaging | `ehr/models/timeline.py` | الإسقاط read-only، provenance/version/status، minimum necessary، cursor pagination، ورفض draft/unreleased من العرض للمواطن. |

## Slice 06: الوصفة والدواء والصرف

أضيفت هوية دوائية canonical منفصلة عن الوصفة والمخزون. إنشاء الوصفة يتطلب Encounter موجوداً ضمن نفس organization/facility/workspace، ومقدم وصف محدداً من الخادم، وعضوية وصلاحية NIAM سياقية. يمر السجل من `DRAFT` إلى `SIGNED` وفق state machine صريحة. بعد التوقيع لا يوجد update مباشر للمحتوى؛ amendment ينشئ صفاً جديداً versioned مع `supersedes_id` وسبب واضح، ولا يستطيع الصيدلي تغيير نص الوصفة الموقعة.

تستخدم عمليات catalog وprescription وdispensing `CanonicalClinicalCommandGuard` و`Idempotency-Key` و`If-Match` وتدقيقاً canonical. يحدد الخادم المريض والمقدم والسياق، ولا تُقبل هوية أو tenant من صلاحيات الواجهة. ترفض العقود الاستبدال التلقائي وتكرار الدواء، وتضع controlled medication في `PENDING_POLICY_REVIEW` بدلاً من اختراع قواعد قانونية غير موثقة.

في المخزون، كل batch مرتبطة بالمنشأة والسياق، ولها expiry وquantity غير سالبة. كل إتمام صرف يمسك صف batch ويعيد حساب المتبقي للوصفة تحت transaction، ثم ينشئ ledger entry من نوع `DISPENSE`. يسمح partial dispensing، ويرفض batch منتهية أو محجورة أو غير مطابقة للدواء أو غير كافية. يلزم actor مختلف للتحضير والتحقق/الإتمام، ولا توجد واجهة تعديل أو حذف للدفتر.

أضيفت كذلك إسقاطات FHIR read-only لـ`MedicationRequest` و`MedicationDispense`. هذه الإسقاطات لا تمنح صلاحية جديدة؛ تمر عبر نفس authorization وتمنع المواطن من رؤية وصفة draft أو سجل صرف غير مكتمل.

## Slice 07: التصوير الطبي

يمر مسار التصوير من `DRAFT → PLACED → SCHEDULED → IN_PROGRESS → COMPLETED` للطلب، ومن `RECEIVED → MATCHED → ACQUIRED → COMPLETED` للدراسة، ومن `DRAFT → SIGNED → RELEASED` للتقرير. ينشئ الخادم accession number، ولا يعتمد على patient name للمطابقة. تستخدم الدراسة `study_instance_uid` و`source_message_id` وprovenance، مع حماية duplicate ingestion وquarantine بدلاً من auto-match غير الموثوق.

أضيفت واجهات `DICOMAdapter`, `RISAdapter`, و`PACSAdapter` مع `SyntheticImagingAdapter` deterministic للاختبار فقط. لا يُستدعى PACS أو RIS أو DICOM حقيقي، ولا تُخزن binary images في PostgreSQL، ولا تقبل schemas روابط `http` أو `https` عامة. التقرير النهائي immutable؛ التصحيح amendment جديد versioned، والنتيجة الحرجة تنشئ notification intent داخلياً/اصطناعياً وتحتاج acknowledgement قبل الإغلاق.

أضيفت projections FHIR لـ`ServiceRequest` و`ImagingStudy` و`DiagnosticReport` كقراءة محمية. مشاركة التقرير المنشور تمر عبر Slice 05 Access Grant، ولا توجد public URL أو مشاركة مستقلة.

## Slice 08: Unified Clinical Record

السجل الموحد ليس patient database ثانية. يقوم `ClinicalRecordService` بجمع مصادر canonical الحالية فقط: Encounter وClinical Note الموقعة، Lab Result المنشور، Prescription الموقعة أو المعدلة، Dispense المكتمل/الجزئي، Imaging Study المكتملة، وImaging Report المنشور. لا يعرض draft notes أو unreleased results أو draft reports للمواطن.

يُفرض الوصول على الخادم باستخدام self-patient أو علاقة provider موثقة أو Access Grant قائم له purpose و`read_record` scope وexpiry. الاستجابة minimum-necessary وتحتوي source domain وsource id وversion وprovenance وstatus. يستخدم timeline cursor opaque مبنياً على التاريخ والمعرف، مع حد أقصى للصفحة، ولا يوجد offset غير محدود في هذا المسار. كل قراءة تسجل `CLINICAL_RECORD_VIEWED` في التدقيق canonical.

## أدلة التحقق الحالية

| الدليل | النتيجة | حدود الدليل |
|---|---:|---|
| Pharmacy API: prescription signing/amendment وdispensing safety | `2 passed` | SQLite TestClient؛ ليس multi-worker proof. |
| Imaging API: lifecycle وDICOM duplicate/public URL وFHIR وsharing | `3 passed` | metadata اصطناعية فقط؛ لا PACS/RIS حقيقي. |
| Unified Record API: filtering وcursor وauthorization | `3 passed` | read aggregation محلي، لا staging consistency proof. |
| Synthetic core backend بعد توسيع الشرائح | `9 passed` | fixture test-only، لا persistence production. |
| Focused regression لـSlice 03–08 والعقود وinventory | `27 passed, 1 warning` | دليل محلي مركز. |
| Full backend suite | `2814 passed, 5 skipped, 165 warnings` خلال `309.98s` | نتيجة محلية؛ لا تعادل remote CI أو staging. |
| PostgreSQL 16.15 disposable | upgrade head وschema gate ناجحان | قاعدة محلية مؤقتة فقط. |
| PostgreSQL rollback/re-upgrade | downgrade إلى `20260828_0013` ثم upgrade إلى `20260828_0014` ناجح | لا يثبت rollback production أو HA. |
| PostgreSQL pharmacy stock-lock probe | `pass`: نتيجتان `conflict,winner` والكمية النهائية `0` | إثبات primitive متعدد الاتصالات؛ لا يثبت multi-worker API أو staging. |
| Engineering Inventory | `1961` ملفاً، `READY_FOR_REVIEW` | advisory؛ أبقى `production_ready=false`. |

## ما لم يُفتح عمداً

لم تُفتح أي كتابة سريرية في frontend أو public demo، ولم تستخدم بيانات مواطنين حقيقية أو credentials أو PACS/LIS/RIS/HIS أو Telegram/SMS/WhatsApp. لم تُنشأ قواعد controlled-medication قانونية غير معتمدة، ولم يُنفذ automatic substitution أو remote delivery أو public image hosting. كما لم يحدث merge أو force-push أو production deployment، ويبقى PR #250 Draft.

## فجوات ما قبل staging والإنتاج

ما زال يلزم تشغيل remote CI مع logs قابلة للقراءة، واختبار staging بقاعدة PostgreSQL حقيقية مع rollback معتمد، وإثبات concurrency متعدد العمال عبر API للصرف وingestion وAccess/Record؛ فـstock-lock probe الحالي يثبت primitive قاعدة البيانات فقط. يلزم كذلك اختبار rate-limit/Redis HA/failover، ومراجعة مستقلة لـIAM object authorization والتوقيع الرقمي وMFA. يلزم أيضاً قرار owner/deprecation رسمي لمسارات legacy pharmacy/radiology/EHR، واختبارات frontend/browser E2E بعد اعتماد عقود الكتابة، وقياس أداء production-like لا يختصر authorization أو audit.

## مراجع التنفيذ داخل المستودع

1. [Clinical state contracts](../../backend/app/contracts/clinical_core.py)
2. [Canonical pharmacy package](../../backend/app/clinical/pharmacy/)
3. [Canonical imaging package](../../backend/app/clinical/imaging/)
4. [Unified Clinical Record package](../../backend/app/clinical/record/)
5. [Canonical access package](../../backend/app/clinical/access/)
6. [Migration 0014](../../backend/migrations/versions/20260828_0014_pharmacy_imaging_core.py)
7. [Pharmacy API tests](../../backend/tests/test_core_pharmacy_api.py)
8. [Imaging API tests](../../backend/tests/test_core_imaging_api.py)
9. [Clinical Record API tests](../../backend/tests/test_clinical_record_api.py)
10. [Synthetic core tests](../../backend/tests/test_synthetic_core_backend.py)
11. [Advisory Engineering Inventory](../../backend/app/contracts/engineering_inventory.py)

**الخلاصة:** أصبحت شرائح 06–08 قابلة للمراجعة محلياً بحدود canonical واختبارات ودليل PostgreSQL disposable، لكن لم تُعلن جاهزية إنتاجية ولم تُفتح التكاملات أو الكتابات العامة. هذا الفصل بين ما تم إثباته وما لم يتم إثباته مقصود لحماية سلامة الرحلة السريرية.
