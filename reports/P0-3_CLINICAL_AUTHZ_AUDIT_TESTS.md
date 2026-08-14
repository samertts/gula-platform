# P0-3 — Authorization, Scope, Audit, and Test Gates

## التفويض

يستدعي gateway `AuthorizationDecisionService` داخل مسار القراءة نفسه بعد اشتقاق NIAM organization/facility/workspace وmembership. يستخدم العقد permission keys `patients.read` و`orders.read`. لم تنشئ migration أي role assignments تلقائية، ولذلك لا يحصل أي مستخدم على قدرة جديدة بمجرد تطبيق schema.

## العزل

يُرفض الطلب عند غياب active workspace أو membership أو legacy account link وحيد أو reviewed NIAM mapping. وتُحقن scope predicates داخل service query قبل pagination، مع مطابقة mapping إلى سياق NIAM والـoperational facility والorganization. لا توجد قراءة تسمح بتمرير `lab_id` أو role أو actor ID من العميل.

## canonical audit

يسجل gateway أحداث `clinical_gateway_access` داخل `CanonicalAuditService` ببيانات actor وorganization وfacility وworkspace وrequest/correlation IDs وdecision وreason code وdata classification. وتُسجل حالات الرفض بصيغة deny. تعطل سجل التدقيق يؤدي إلى `503` ولا يسمح بإرجاع بيانات سريرية.

## migration

`20260814_0007_clinical_gateway_scope.py` تضيف `niam_organization_id` و`niam_facility_id` إلى bridge table وتضيف permission catalog entries فقط. الأعمدة nullable عمدًا؛ null يعني أن mapping لم يُراجع بعد وأن gateway يجب أن يبقى محجوبًا. downgrade يزيل العلاقات والمفاتيح دون حذف بيانات clinical.

## الاختبارات

تثبت الاختبارات أن cursor موقّع ومربوط بالمورد ومساحة العمل والـlimit، وأن rollout default هو `OFF`، وأن missing mapping يحجب قبل تشغيل proof أو clinical query، وأن deny authorization لا ينفذ query، وأن patient response لا يعيد phone أو national ID أو lab ID. كما يثبت contract test أن response typed ويقتصر على الحد الأدنى.

اختبار PostgreSQL يثبت columns وpermissions وعدم إنشاء role assignments. يُنفذ هذا الاختبار داخل CI مع migration head، بينما يُتخطى محليًا عند عدم توفر PostgreSQL الحقيقي؛ هذا skip ليس دليل نجاح schema محلي.

## CI

أضيفت ملفات gateway إلى Ruff وcompile/test gates، وأضيف migration test إلى PostgreSQL gate، كما أضيفت اختبارات العقد والـgateway إلى security regression job. لم يتم فتح أي endpoint عبر frontend إلا من خلال allowlist صريحة.

## الحدود

لا يغطي هذا PR النتائج أو العينات أو أي write operation أو اعتماد نتيجة. ولا يثبت تكافؤ Flutter/Android/iOS، ولا يضيف role assignments، ولا يحدد RPO/RTO أو retention قانوني.
