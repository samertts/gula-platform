# أدلة تدقيق مسار الطبيب — 18 آب/أغسطس 2026

## نطاق التدقيق الحالي

تمت مراجعة `frontend-v3/src/routes/index.tsx`، و`ClinicalWorkspacePage.tsx`، و`ResultsPage.tsx`، و`backend/app/clinical_gateway/routes.py`، و`clinical_gateway/context.py`، و`backend/app/routes/clinical_documentation.py`، و`backend/app/routes/clinical_orders.py`، و`backend/app/routes/clinical.py`، و`backend/app/security/dependencies.py`، وتسجيل المسارات في `backend/app/factory.py`.

## المسار الفعلي المثبت

1. الدخول يمر من `ProtectedRoute` في الواجهة، بينما التحقق الخادمي يمر من JWT/session dependency.
2. صفحة `/clinical-workspace` محروسة في الواجهة بواسطة `RoleGuard` على قائمة `readonlyRoles` التي تشمل `doctor` و`staff` و`lab_staff` و`demo_viewer`، وليست صلاحية سريرية دقيقة.
3. `ClinicalWorkspacePage` يقرأ المرضى والطلبات من `workspaceScopedReads` فقط، ويعرض نتائج الطلب المختار عبر `/api/v1/clinical/orders/{numeric_id}/results`.
4. البوابة canonical تستعمل `get_current_niam_actor_sync`، ثم تثبت session/workspace/organization/facility/membership/legacy link/facility binding/tenant scope، وتكتب تدقيقاً عند المنع.
5. صفحة `/results` القديمة لا تعرض نتائج؛ هي `LegacyRouteBridge` فقط، وتناقض الواجهة الجديدة التي تعرض `results.read` داخل Clinical Workspace.
6. backend يسجل أيضاً مسارات legacy `/clinical/orders` و`/clinical/documentation`، إضافة إلى `/clinical` الكبير، بالتوازي مع `/api/v1/clinical` canonical.

## نتائج عالية الخطورة مثبتة من المصدر

### 1. مسارات التوثيق السريري legacy غير مرتبطة بقاعدة بيانات أو نطاق مؤسسة

`backend/app/routes/clinical_documentation.py` يخزن المستندات في `_DOCUMENTS` و`_VERSION_HISTORY` داخل ذاكرة العملية. هذا يعني فقدان البيانات عند إعادة التشغيل، وعدم التوزيع الآمن بين workers، وعدم وجود transaction أو migration أو backup أو audit durable.

الدوال `list_documents` و`get_document` و`get_document_version_history` تعتمد على `get_current_user` فقط، ولا تفلتر بـ`current_user.lab_id` أو organization/facility/workspace، ولا تثبت أن الطبيب جزء من فريق المريض. إنشاء المستند يقبل `patient_id` و`encounter_id` من العميل، ويخزن `created_by` فقط.

`sign_document` يسمح للمستخدم الحالي بتوقيع أي document_id موجود في الذاكرة، من دون إثبات أن المستخدم هو المؤلف أو طبيب مخول في نفس المؤسسة أو أن المستند قابل للتوقيع من دوره. `role` و`signature_type` من العميل ولا يظهر حارس صلاحية سريرية أو توقيع قوي.

### 2. مسارات clinical orders legacy غير مرتبطة بقاعدة بيانات أو نطاق مؤسسة

`backend/app/routes/clinical_orders.py` يخزن الطلبات والقوالب والطلبات المتكررة والتعيينات في `_FAKE_ORDERS` وذاكرات عامة مماثلة. `list_orders` يجمع كل الذاكرة ثم يفلتر اختيارياً بـ`patient_id` و`encounter_id` و`status`، لكنه لا يفلتر بـ`lab_id` بعد إنشاء السجلات؛ لذلك يمكن لمستخدم authenticated رؤية سجلات كل المختبرات الموجودة في نفس process.

`get_order` و`cancel_order` و`complete_order` تقبل order_id فقط وتتحقق من وجوده، لا من ملكية المختبر أو المنشأة أو الصلاحية. يمكن للمستخدم المصادق عليه إلغاء أو إكمال طلب لا ينتمي إلى مؤسسته إذا عرف المعرف.

الطلب يقبل `patient_id` و`ordering_provider_id` و`status` و`metadata` من العميل. لا يوجد إثبات server-side أن المريض داخل نطاق الطبيب أو أن ordering provider هو المستخدم الحالي أو أن الحالة الابتدائية مسموحة للدور.

### 3. غياب صلاحيات دقيقة عن كثير من مسارات `/clinical`

`backend/app/routes/clinical.py` يستخدم `get_current_user` في مسارات terminology/knowledge/CDS/quality/research. وجود جلسة `LabUser` لا يساوي صلاحية طبيب أو صلاحية محرر بروتوكول أو مسؤول جودة. توجد عمليات إنشاء وتعديل وحذف وموافقة مثل terminology codes وguidelines وprotocols وpathways وstanding orders وclinical alerts وquality records، لكن dependency الظاهرة ليست `require_permission` أو بوابة مؤسسة canonical.

### 4. فجوة بين قائمة أدوار الواجهة والتفويض الخادمي

`readonlyRoles` يسمح لـ`doctor` و`staff` و`lab_staff` و`demo_viewer` بالوصول إلى Clinical Workspace. هذا حارس عرض وليس مرجعاً أمنياً. الخطر العملي هو أن الواجهة توحي بأن كل هذه الأدوار تملك نفس المساحة، بينما البوابة الخادمية قد تمنع بعض الحالات بسبب workspace/membership/legacy mapping. يجب اعتبار هذا UX/authorization parity gap حتى تتم مصفوفة أدوار server-side لكل contract.

### 5. تقاطع مسارات متوازية للنتائج والطلبات

يوجد `/results` في الواجهة لكنه bridge، و`frontend-v3/src/api/endpoints.ts` يحتوي clients عامة لمسارات legacy، بينما `workspaceScopedReads` يحصر القراءة canonical. هذا يخلق surface مزدوجاً واحتمال إعادة استخدام client قديم في شاشة جديدة. الإغلاق الصحيح هو إزالة أو تعطيل كل client/route legacy السريري أو جعله يعيد 410/redirect محروساً بعد إثبات عدم وجود consumers.

## قيود مثبتة في المسار الحالي

Clinical Workspace قراءة فقط تقريباً: لا توجد فيه زيارة سريرية كاملة، لا SOAP note، لا وصفة، لا إحالة، لا اعتماد نهائي، ولا discharge workflow. صفحات capabilities تعرض قدرات عامة أو API surfaces وليست مسار طبيب قابل للتنفيذ من البداية إلى النهاية. لذلك الوصف الصحيح هو clinician read workspace، وليس EHR/doctor workflow مكتمل.

## عناصر تحتاج تدقيقاً إضافياً

- خدمات الوصفات والصيدلية: ownership، prescribing role، interactions، substitution approval، citizen medication record.
- مسارات المواعيد والزيارات والإحالات: tenancy، participant authorization، state transitions، double booking.
- clinical service/CDS والـquality/research: filtering والحدود بين physician وlab staff وadmin.
- patient card وpatient management: هل تتجاوز gateway canonical أو تبني scope من client ids؟
- الأجهزة والنتائج القادمة من gateway: ربط device event بالمؤسسة والطلب والمريض، ورفض raw payload.
- mobile/desktop parity: لا يوجد دليل تشغيل native على current head؛ تبقى UNVERIFIED.

## الحالة المؤقتة

P4 لا يُغلق بسبب هذه الفجوات حتى لو اجتازت الاختبارات المحلية. لا يجوز فتح P5 قبل إصلاح أو إيقاف المسارات legacy الحساسة، وإثبات دور الطبيب والمؤسسة server-side، وإتمام تدوير مفتاح Android وتحقق native CI.

## أدلة إضافية من السطح المرئي والتكاملات

### 6. Patient Management Workspace ليس مساراً تشغيلياً

`frontend-v3/src/pages/patients/PatientManagementWorkspacePage.tsx` يبني `INITIAL_PATIENTS` و`INITIAL_APPOINTMENTS` و`INITIAL_QUEUE` داخل bundle، ويجعل التسجيل والتحديد وتحديث القائمة state محلياً. الشاشة تعرض أرقام هواتف ومعرفات صحية اصطناعية، وتصرح بنفسها أن البيانات لا تُرسل خارجياً وأن التسجيل تجريبي فقط. وجود هذه الصفحة تحت `/patient-management` مع `readonlyRoles` قد يجعل الطبيب يظن أن التسجيل والمواعيد وقائمة الانتظار عمليات حقيقية، رغم عدم وجود request أو audit أو server decision.

### 7. بطاقة المريض مسار legacy يعرض بيانات أكثر من canonical DTO

`frontend-v3/src/pages/patient-card/PatientCardPage.tsx` يسمح بإدخال رقم مريض رقمي من العميل ثم يستدعي `patientCardApi.get`، ويعرض `full_name` و`phone` و`health_id` وQR، ويفتح `/api/patient-card/{id}/print` مباشرة. هذا يتعارض مع `patients.read` canonical الذي يمنع الهاتف والـnational identifiers من DTO، ويخلق مساراً موازياً لمسار الطبيب.

Backend `patient_card.py` يثبت `lab_id` ويضع rate limit وaudit وHMAC binding، وهي نقاط قوة حقيقية، لكنه يعيد `token` و`qr_url` في card retrieval ويعرض بيانات هوية مطبوعة. كما أن dependency المعلنة هي `get_current_user` وليست `require_institutional_user` أو قراراً سريرياً يثبت workspace/role/relationship؛ لذلك يجب اختبار سلوك User/citizen token صراحة وعدم الاعتماد على type annotation `LabUser` وحده.

### 8. Pharmacy prescriptions ليست محكومة بدور الطبيب

`pharmacy/routes.py` يستخدم `get_current_user` لمعظم prescription وdispense وclinical checks، بينما يستخدم `require_institutional_permission` صراحة لمسارات POS المالية فقط. `create_prescription` يقبل `prescriber_id` من payload، و`PharmacyService.create_prescription` ينسخ الحقول المسموحة ويضع `lab_id` إن وجد دون إثبات أن prescriber_id يساوي الطبيب الحالي أو أن دور الحساب يسمح بالوصف.

`get_prescription` وstatus/renew/cancel/add-item تعتمد على lab filter في الخدمة عند وجود `lab_id`، لكنها لا تحقق transition policy سريرية أو ownership للطبيب أو dual control للصرف. `substitute_prescription_item` يبحث عن item عبر `item_id` و`rx_id` فقط، ثم يغير الدواء؛ لا يظهر في المقطع المقروء تحقق من أن الوصفة تخص المختبر الحالي قبل lookup item، ولا تحقق من `substitution_allowed` أو موافقة الصيدلي أو تسجيل سبب الاستبدال وسجل المواطن.

### 9. مسار Patient Visit معلن صراحة أنه غير تشغيلي

`PatientVisitReadinessPage.tsx` يضع Check-in وQueue وEncounter وpatient view في `BACKEND_DEPENDENCY`، ويضع Triage وEncounter-linked results وClose Encounter في `BLOCKED`. الصفحة لا تجلب بيانات ولا تنفذ mutations. لذلك لا يستطيع الطبيب حالياً تنفيذ دورة زيارة كاملة من check-in إلى encounter ثم triage/notes/results/review/close.

### 10. التناقض في حراس الواجهة

`/clinical-workspace` و`/orders` و`/patient-management` و`/pharmacy-operations` و`/billing-insurance` تحت `readonlyRoles`، وهي قائمة تشمل doctor وstaff وlab_staff وdemo_viewer، بينما `/pharmacy` الإداري تحت `adminRoles` فقط. هذا تصنيف UI عام، وليس بديلاً عن server-side permissions. كما توجد capabilities كثيرة تحت `dashboard:read` تعرض surfaces سريرية، ما يخلط بين اكتشاف القدرة وتنفيذ عملية سريرية.

## مصفوفة أولية للرحلة

| مرحلة الطبيب | السطح الحالي | الحقيقة التشغيلية | الخطر/العائق |
|---|---|---|---|
| الدخول | Login + ProtectedRoute + backend JWT | موجود، لكن نجاح الدخول لا يثبت workspace سريري | يلزم session/workspace/role parity |
| اختيار workspace | `/clinical-workspace` + ClinicalGateway | أقوى جزء؛ context resolver يثبت المؤسسة والمنشأة والعضوية والربط القديم | legacy identity mapping قد يمنع الطبيب الصحيح |
| دليل المرضى | `/patients` canonical | قراءة DTO دنيا فقط | لا توجد patient relationship/assignment UI واضحة |
| بطاقة المريض | `/patient-card` legacy | قراءة lab-scoped مع phone/health_id/QR token | مسار موازٍ، بيانات أكثر، role/workspace gap |
| إدارة المرضى | `/patient-management` | demo local state | لا بيانات حقيقية، خطر التباس تشغيلي |
| الطلبات | `/orders` canonical | قراءة فقط | لا إنشاء/تعديل/اعتماد من المسار canonical |
| النتائج | `/clinical-workspace` results.read | قراءة طلب محدد فقط | `/results` القديم bridge، ولا review/sign/approve |
| الزيارة | `/patient-visit/readiness` | prototype/status only | check-in/triage/encounter/close محجوب |
| التوثيق | `/clinical/documentation` legacy | in-memory وget_current_user فقط | تسريب نطاق، فقدان بيانات، توقيع غير محكوم |
| الوصفة | `/pharmacy/prescriptions` | backend service مع lab filter جزئي | لا role/prescriber proof ولا dual control كامل |
| الإحالة/الموعد | surfaces citizen/national متعددة | لا surface طبيب canonical مثبت | تكرار models/routes وغياب end-to-end proof |
| الخروج | لا encounter close / visit summary canonical | غير مكتمل | لا سجل نهائي server-confirmed |

## تصنيف أولي للخطورة

- **حرج:** legacy clinical documentation/orders تسمح بعمليات حساسة مع get_current_user فقط وبـglobal in-memory stores، وعمليات التوثيق/التوقيع لا تثبت ملكية أو صلاحية المؤسسة.
- **عالٍ:** patient-card وpharmacy prescription surfaces موازية لمسار canonical؛ card يعرض token/phone/health_id، والوصفة تقبل prescriber_id من العميل وتتيح status/renew/cancel/substitution دون role-specific proof ظاهر.
- **متوسط:** demo patient-management وcapabilities surfaces قد تسبب التباساً بين prototype والتشغيل، وتوجد فجوة parity بين readonlyRoles والصلاحيات الخادمية.
- **محجوب تشغيلياً:** Patient Visit الكامل، triage، encounter close، review/approve results، mobile/desktop parity، Android signing incident، وCI الحالي.

## قاعدة التقرير

لم تُعتبر أي ملاحظة runtime vulnerability مثبتة باختبار HTTP حي في هذه المرحلة؛ الملاحظات المبنية على source inspection توسم **Source-confirmed / Runtime-unverified** إلى أن تضاف negative tests مستقلة لكل endpoint.
