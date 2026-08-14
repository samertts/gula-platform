# P0-2 — Clinical Read Gateway Core

## النطاق

ينفذ هذا التغيير البوابة الخادمية versioned للقراءات `patients.read` و`orders.read` فقط. لا يضيف أي عملية كتابة أو اعتماد نتيجة، ولا يزيل مسارات legacy أو يجعلها مصدرًا للواجهة الجديدة. تبقى قيمة rollout الافتراضية `OFF`، وتبقى bridge rows غير المربوطة بسياق NIAM محجوبة.

## مسار الثقة

يبدأ الطلب من `get_current_niam_actor_sync` الذي يتحقق من token و`account_uuid` و`jti` وحالة الحساب والجلسة النشطة. بعد ذلك يثبت `WorkspaceSessionContext` النشط، ثم يتحقق من workspace وorganization وfacility في NIAM، ثم من membership النشطة، ثم من `LegacyAccountLink` الوحيد بحالة `migrated`.

لا يقبل gateway أي `organization_id` أو `facility_id` أو `workspace_id` من query أو body. ويُشترط وجود reviewed mapping في `clinical_lab_facility_bindings` إلى `niam_organization_id` و`niam_facility_id`، مع status فعال وmapping version. عند غياب mapping أو تعدده، تكون النتيجة `BLOCKED_SAFE`.

## adapter وحدود البيانات

يستخدم gateway الخدمات legacy الحالية بعد تمرير `ClinicalLegacyReadScope` مشتق خادميًا. أضيفت scope predicates داخل patient/order queries قبل `count` وpagination، وتشمل legacy lab، operational facility، operational organization، وNIAM mapping. لا يستخدم gateway `lab_id` أو role أو user ID من العميل.

الاستجابة typed ومحدودة؛ patient read لا يعيد phone أو national identifier أو lab ID، وorder read لا يعيد results أو patient/lab identifiers legacy. pagination تستعمل cursor موقّعًا ومربوطًا بالمورد ومساحة العمل وحجم الصفحة.

## rollout

يتحكم backend في الحالات `OFF`, `INTERNAL`, `PILOT`, `ON` عبر environment variables وallowlists server-side. لا يستطيع browser تغيير الحالة. `OFF` هو default، ووجود route في OpenAPI لا يعني أن القراءة مفعلة.

## متطلبات التشغيل المتبقية

يجب تطبيق migration `20260814_0007` على PostgreSQL، وإضافة reviewed mappings يدويًا عبر حوكمة معتمدة قبل اختيار أي organization أو account في `INTERNAL` أو `PILOT`. لا تنشئ migration أي role assignment تلقائي، ولا تدعي موافقة حكومية أو امتثالًا قانونيًا.

## الملفات الأساسية

تشمل الملفات `backend/app/clinical_gateway/*`، و`ClinicalLabFacilityBinding` mapping fields، و`ClinicalLegacyReadScope`، وتعديلات patient/order adapters، وتسجيل router في factory، وتوفير sync actor dependency للحدود الحالية ذات SQLAlchemy Session.

## الحالة

هذا PR يثبت gateway core لكنه لا يفتح rollout production. الاختبارات والـcanonical audit gates موثقة في PR-2، وربط frontend-v3 موثق في PR-3.
