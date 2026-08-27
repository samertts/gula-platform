# تنفيذ مسار المختبر الطبي في GULA

## النطاق المنفذ

تم تحصين صفحة `LabOperationsWorkspacePage` داخل `frontend-v3` لتصبح طبقة عرض مختبرية تفصل بوضوح بين Demo الاصطناعي والمعزول وبين Live المرتبط بعقود GULA الحالية. لا تنشئ الواجهة مريضاً أو طلباً أو عينة أو نتيجة أو جهازاً أو سجل جودة، ولا تعتبر زر الواجهة بديلاً عن state machine أو التفويض الخادمي.

> **قاعدة التشغيل:** لا يجوز أن تتحول العينة أو النتيجة إلى حالة سريرية معتمدة من state محلي في React. الـbackend هو مصدر الحقيقة، وسلسلة الحيازة والتدقيق والنسخ والتصحيح يجب أن تكون خادمية.

## الوضع التجريبي Demo

يعرض Demo رحلة المختبر كاملة لأغراض المشاهدة فقط: الطلب والوصول، سلسلة حيازة العينة، النتائج الأولية والحرجة، المحللات والبروتوكولات، وضبط الجودة. البيانات اصطناعية ولا تُرسل إلى OpenELIS أو محلل أو خدمة خارجية.

أزيلت أزرار «محاكاة التحقق» و«بدء الفحص» من السلوك التنفيذي. يمكن للمستخدم التنقل والبحث والاطلاع على السيناريو، لكن لا يستطيع إنشاء أثر سريري أو تغيير حالة عينة أو إصدار نتيجة. هذا يحافظ على Demo كبيئة قراءة فقط بدلاً من محاكاة قد توحي بأن التحقق تم فعلاً.

## الوضع الحي Live

لا تستخدم الصفحة بيانات Demo كبديل في Live. تبدأ بـ`GET /niam/workspaces` ثم تعرض مساحات منشآت مؤهلة فقط. لا يتم تفعيل السياق إلا عبر `POST /niam/workspaces/{workspace_id}/switch`، وبعد اختيار سياق خادمي صالح تستخدم الواجهة القراءة المعتمدة الحالية من `workspaceScopedReads.listOrders({ limit: 50 })`.

تظهر الطلبات كملخص محدود عبر clinical gateway؛ لا تُعرض النتائج أو العينات أو الحالة التشخيصية من هذا المسار. عند غياب مساحة مختبر مؤهلة أو عند فشل التبديل أو القراءة، يظهر حجب واضح ولا يحدث fallback إلى endpoints legacy.

## العقود المؤجلة عمداً

العقود التالية لا تتوفر حالياً في canonical clinical gateway للمختبر، ولذلك بقيت محجوبة في Live:

| المجال | سبب الحجب |
|---|---|
| Specimen وAccession وBarcode | يحتاج عقداً يفرض patient/order/tube matching، chain-of-custody، actor، الموقع، الوقت، وسبب الرفض. |
| قبول ورفض العينة وإعادة الجمع وAliquot | يحتاج state machine خادمية تمنع الحذف وتربط recollection بالأصل وتفرض version/idempotency/audit. |
| Worklists ونتائج الفنيين | تحتاج صلاحية section/facility ونطاق عمل لا يستنتج من role الواجهة. |
| Analyzer Gateway وASTM/HL7/FHIR mapping | يحتاج gateway معزولاً، registry، mapping، idempotency، replay protection، calibration، وفصل الجهاز عن قاعدة البيانات. |
| QC وCalibration وMaintenance وCAPA | تحتاج domain مستقلاً وقواعد hold/release وتحقيقاً قابلاً للتدقيق. |
| Observation وDiagnosticReport وRelease | تحتاج التحقق، المجال المرجعي، flags، critical workflow، النسخ والتصحيحات، وسياسة إتاحة للمواطن والطبيب. |
| Critical Notification وAcknowledgment | لا يكفي Push؛ يلزم delivery/acknowledgment/escalation وسجل تدقيق وسياسة قناة. |
| Offline queue | لا تُضاف قبل عقد encrypted queue ومزامنة server validation وحل التعارض domain-specific؛ لا يُستخدم Last Write Wins للبيانات الطبية. |
| Billing وInventory وPublic Health | تبقى منفصلة عن نموذج النتيجة وتحتاج purpose وtenant/role/legal scope مستقلاً. |

## العزل والصلاحيات

وجود المستخدم في `lab_admin` أو `lab_staff` أو دور مؤسسي لا يكفي وحده لمنحه اعتماد نتيجة أو قراءة كل فروع المختبر. يجب أن يثبت الخادم professional verification وmembership وfacility/department scope والسياسة التشغيلية. كما لا تمثل barcode هوية المريض ولا توفر authentication، ولا ينشئ LIS هوية المواطن إذا كانت موجودة في GULA.

لا تقوم الصفحة بإنشاء نتيجة أو تعديلها بواسطة `setState`، ولا تعرض زر إصدار أو تحقق في Live. علي رضا غير مضاف كصاحب قرار في هذه الموجة؛ أي مساعد لاحق يمكنه شرح الحالة أو اكتشاف نقص إجرائي فقط، ولا يجوز له تغيير قيمة أو تجاوز critical workflow أو release.

## التحقق المنفذ

أضيفت اختبارات تثبت أن Demo لا يستدعي `listWorkspaces` أو clinical gateway، وأن Live لا يقرأ الطلبات قبل تبديل سياق خادمي، وأنه يستخدم canonical clinical gateway بعد التبديل، وأن تبويبات العينات والنتائج والمحللات والجودة تعرض الحجب بدلاً من اختلاق عقود LIS.

## الخطوات backend-first التالية

قبل فتح أي واجهة كتابة أو قراءة تفاصيل، يجب تصميم OpenAPI وعقود backend لـ`Specimen/Accession` و`Result/Observation/DiagnosticReport` و`QC/Analyzer` و`Critical Notification`، ثم إضافة اختبارات tenant isolation وRBAC سياقي وstate transitions وoptimistic concurrency وidempotency وimmutable audit وbackup/restore rehearsal. بعد ذلك فقط يمكن توصيل الواجهة، مع إبقاء feature flags مغلقة افتراضياً في Demo.
