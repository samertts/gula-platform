# التدقيق الكامل لمسار الطبيب داخل منصة GULA

**تاريخ التدقيق:** 18 آب/أغسطس 2026

**الفرع المفحوص:** `chore/security-ddos-hardening-clean`

**نطاق التدقيق:** الدخول والهوية، اختيار مساحة العمل، المرضى، بطاقة المريض، الطلبات، نتائج المختبر، الزيارة والـEncounter، التوثيق السريري، الوصفات، الإحالات، المواعيد، الصيدلية، والواجهات المتوازية القديمة والجديدة.

## الحكم التنفيذي

مسار الطبيب في GULA **ليس مساراً سريرياً كاملاً بعد**. الجزء الأقوى حالياً هو بوابة القراءة السريرية canonical، التي تثبت سياق الجلسة ومساحة العمل والمؤسسة والمنشأة والعضوية والربط القديم ونطاق المستأجر قبل قراءة المرضى والطلبات والنتائج. هذا الجزء مدعوم باختبارات محلية ناجحة، لكنه يمثل **قراءة سريرية محكومة** وليس دورة طبيب كاملة.

في المقابل، توجد مسارات legacy مسجلة فعلياً في backend للتوثيق السريري والطلبات، وتحتوي على عمليات كتابة وتوقيع وإكمال وإلغاء تعتمد غالباً على `get_current_user` فقط. كما توجد واجهات موازية لبطاقة المريض والصيدلية وإدارة المرضى، بعضها تجريبي محلي وبعضها يعرض بيانات حساسة أو ينفذ عمليات دون نفس سلسلة إثبات workspace/organization/facility التي تستخدمها البوابة canonical.

> **القرار الأمني:** لا يجوز اعتبار مسار الطبيب جاهزاً للتشغيل السريري أو اعتماد P4 بسبب وجود مسارات legacy قابلة للوصول وفجوة بين الواجهة المحروسة والعقود الخادمية القديمة. تبقى حالة P4 **PARTIAL / SECURITY_BLOCKED**، ويبقى P5 محجوباً.

## 1. مسار الطبيب الفعلي من البداية إلى النهاية

| المرحلة | المسار المرئي أو backend | الحالة الفعلية | الحكم |
|---|---|---|---|
| الدخول | `/login` ثم `ProtectedRoute` ثم JWT/session backend | التحقق من الجلسة موجود، لكن الدخول وحده لا يثبت سياق طبيب أو منشأة | موجود جزئياً |
| اختيار مساحة العمل | `/clinical-workspace` مع `RoleGuard` ثم `ClinicalGatewayContextResolver` | البوابة تثبت session/workspace/organization/facility/membership/legacy link/facility binding/tenant | أقوى جزء؛ قراءة فقط |
| دليل المرضى | `/patients` وداخل Clinical Workspace عبر `patients.read` | DTO دنيا، لا هاتف ولا national identifier، مع سياق مساحة عمل في الاستجابة | PASS محلياً للعقد |
| إدارة المرضى | `/patient-management` | بيانات اصطناعية داخل React state؛ التسجيل محلي ولا يصل للخادم | Demo فقط، وليس EHR |
| بطاقة المريض | `/patient-card` و`/api/patient-card/{id}` | قراءة lab-scoped مع QR/HMAC/audit، لكنها تقبل رقماً من العميل وتعرض phone/health_id/token | مسار legacy موازٍ يحتاج إيقافاً أو توحيداً |
| الطلبات | `/orders` عبر `orders.read` | قراءة canonical فقط، دون إنشاء أو تعديل أو اعتماد | قراءة فقط |
| النتائج | تبويب نتائج الطلب داخل Clinical Workspace عبر `results.read` | يقرأ نتائج طلب مختار، مع DTO دنيا وحظر حقول المشاركة | PASS محلياً للعقد، دون review/approve |
| `/results` القديم | `ResultsPage` يعيد `LegacyRouteBridge` | لا يعرض نتائج فعلية | تناقض واجهة ومسار قديم |
| Check-in والانتظار | `PatientVisitReadinessPage` | prototype بلا API أو mutations؛ مصنف BACKEND_DEPENDENCY | غير تشغيلي |
| Encounter | صفحة جاهزية فقط | لا يوجد request/response contract تشغيلي مثبت | محجوب |
| Triage والعلامات الحيوية | لا surface تشغيلي مثبت | مصنف BLOCKED | محجوب |
| التوثيق السريري | `/clinical/documentation` | endpoints إنشاء/قائمة/توقيع/نسخ، لكن تخزين in-memory وتفويض عام | خطر حرج مرشح |
| الطلبات legacy | `/clinical/orders` | إنشاء/قائمة/إكمال/إلغاء وstanding/recurring في in-memory store | خطر حرج مرشح |
| الوصفة | `/pharmacy/prescriptions` | خدمة DB مع lab filter جزئي، لكن role/prescriber/state policy غير مكتملة ظاهرياً | خطر عالٍ |
| الإحالة والمواعيد | citizen/national/legacy surfaces متعددة | لا يوجد مسار طبيب canonical كامل مثبت من إنشاء الإحالة حتى قبولها وإغلاقها | فجوة تشغيلية وتقاطع نماذج |
| إغلاق الزيارة | لا يوجد surface تشغيلي | المتطلبات وversion conflict وimmutable audit غير مثبتة | محجوب |
| الخروج | لا Visit Summary server-confirmed ولا close encounter | لا يمكن إنهاء الرحلة السريرية رسمياً | غير مكتمل |

المصادر الأساسية لهذا المسار هي خريطة React والـguards [1]، صفحة Clinical Workspace [2]، وعميل القراءة canonical [3]، وبوابة القراءة الخادمية [4] وسياقها [5].

## 2. ما يستطيع الطبيب فعله حالياً

يمكن للطبيب، إذا كانت الجلسة والمطابقة القديمة وسياق مساحة العمل مكتملة، رؤية المرضى والطلبات ونتائج طلب محدد من خلال البوابة canonical. ويمكنه أيضاً رؤية بعض الأسطح العامة أو التجريبية بحسب `RoleGuard`، مثل Patient Management Workspace وPharmacy Operations وBilling/Insurance، لكن هذا لا يعني أن العمليات الموجودة فيها حقيقية أو أن backend يمنح نفس الصلاحيات.

لا يستطيع الطبيب عبر المسار canonical تنفيذ دورة زيارة كاملة، أو تسجيل Check-in حقيقي، أو فتح Encounter موثق، أو إدخال Triage، أو إنشاء SOAP note محكوم، أو اعتماد نتيجة، أو إصدار وصفة مثبتة الهوية، أو إنشاء إحالة سريرية كاملة، أو إغلاق Encounter بتلخيص server-confirmed.

الخطر هنا مزدوج: **نقص تشغيلي** في المسار الصحيح، و**وجود مسارات legacy كتابية** قد تسمح بتنفيذ عمليات حساسة خارج المسار الصحيح إذا عُرف endpoint أو استُخدم client قديم.

## 3. الثغرات والمشاكل المصنفة

### C-01 — مسارات التوثيق السريري legacy بلا عزل مؤسسي دائم

**الخطورة:** حرجة مرشحة، Source-confirmed / Runtime-unverified.

في `backend/app/routes/clinical_documentation.py` تُخزّن المستندات في `_DOCUMENTS` و`_VERSION_HISTORY` داخل ذاكرة العملية. الدوال `list_documents` و`get_document` و`get_document_version_history` تعتمد على `get_current_user` ولا تطبق `lab_id` أو organization/facility/workspace أو patient assignment. إنشاء المستند يقبل `patient_id` و`encounter_id` من العميل، ولا يثبت أن المريض يقع في نطاق الطبيب.

`sign_document` يسمح بتوقيع `document_id` موجود في الذاكرة دون إثبات مؤلف المستند أو دور الطبيب أو عضويته في المؤسسة. كما أن `role` و`signature_type` تأتي من payload. التخزين يضيع مع إعادة التشغيل ولا يضمن الاتساق بين workers أو audit durable أو backup.

**الأثر المحتمل:** قراءة أو تعديل أو توقيع مستندات من نطاق مؤسسة أخرى داخل نفس عملية التشغيل، مع فقدان المستندات عند restart، وانهيار الثقة في السجل السريري.

**الإصلاح:** إيقاف endpoints مؤقتاً أو إرجاع 410/503 محكوم، ثم نقل المستندات إلى جداول durable مرتبطة بـorganization/facility/workspace/patient/encounter، وإنشاء صلاحيات منفصلة للإنشاء والتعديل والتوقيع، مع immutable audit وoptimistic locking.

### C-02 — مسارات الطلبات legacy تستخدم global in-memory store وتسمح بعمليات حالة عامة

**الخطورة:** حرجة مرشحة، Source-confirmed / Runtime-unverified.

في `backend/app/routes/clinical_orders.py` تُخزّن الطلبات في `_FAKE_ORDERS`، والقوالب والطلبات المتكررة والتعيينات في هياكل ذاكرة مماثلة. `create_order` يكتب `lab_id` من المستخدم، لكن `list_orders` و`get_order` و`cancel_order` و`complete_order` لا تستخدم هذا الحقل لفرض العزل. وجود المعرف وحده يكفي للوصول إلى الطلب أو إلغائه أو إكماله بعد المصادقة العامة.

الطلب يقبل `patient_id` و`ordering_provider_id` و`status` و`metadata` من العميل. لا يوجد في هذه الوحدة إثبات أن ordering provider هو الطبيب الحالي، أو أن الحالة الابتدائية مسموحة، أو أن المريض داخل نطاق المؤسسة.

**الأثر المحتمل:** قراءة أو تغيير حالة طلب من مختبر آخر، وتسجيل قرار سريري باسم provider يختاره العميل، وتضارب بين الحالة الظاهرة في canonical read والحالة المعدلة في legacy store.

**الإصلاح:** إيقاف كل الكتابات legacy، ثم بناء Clinical Order Command Service durable يفرض actor/workspace/tenant/role، ويدير state machine وidempotency وversion conflict وaudit.

### C-03 — وحدة `/clinical` الكبيرة تعتمد على المصادقة العامة في عمليات كتابة حساسة

**الخطورة:** عالية.

`backend/app/routes/clinical.py` يحتوي عشرات نقاط النهاية للـterminology والـknowledge وCDS والـquality والـresearch. النمط الظاهر هو `get_current_user`، مع غياب `require_permission` أو `get_current_niam_actor` أو بوابة workspace في هذه الوحدة. توجد عمليات إنشاء وتعديل وحذف وموافقة guidelines/protocols/pathways/standing orders، وإنشاء alerts وquality records، ولا يكفي وجود حساب `LabUser` لإسناد كل هذه الصلاحيات.

**التناقض:** وصف المنصة يقول deny-by-default، بينما هذه الوحدة تقدم سطحاً واسعاً لصاحب جلسة عامة من دون تقسيم واضح بين الطبيب والمختبري ومسؤول الجودة ومدير النظام.

**الإصلاح:** تقسيم الوحدة إلى read contracts عامة محدودة، وcommand contracts متخصصة، وإضافة صلاحيات خادمية دقيقة مع organization/facility/workspace scope وتدقيق قرار كل كتابة.

### C-04 — بطاقة المريض مسار موازٍ يعرض بيانات حساسة أكثر من DTO canonical

**الخطورة:** عالية.

واجهة `/patient-card` تقبل إدخال numeric patient ID من العميل، وتعرض الاسم والهاتف و`health_id` وQR، وتفتح طباعة مباشرة عبر `/api/patient-card/{id}/print`. backend يطبق lab isolation وHMAC token وrate limit وaudit، وهي عناصر جيدة، لكنه يعيد `token` و`qr_url` من endpoint القراءة ويقدم full history.

الحارس هو `get_current_user` مع annotation `LabUser`، وليس dependency صريحاً يرفض User/citizen أو يثبت workspace/role/relationship. لا ينبغي اعتبار annotation ضماناً أمنياً. كما أن المسار لا يستخدم DTO الحد الأدنى المستخدم في `patients.read`.

**الإصلاح:** توحيد بطاقة المريض خلف policy-filtered canonical contract، منع token من JSON، استخدام capability قصيرة العمر ومحدودة الغرض، وإخفاء الهاتف والمعرّفات إلا بصلاحية صريحة وتدقيق إضافي.

### C-05 — الوصفة لا تثبت هوية الواصف وصلاحيته على مستوى العملية

**الخطورة:** عالية.

معظم مسارات `/pharmacy` تستخدم `get_current_user`، بينما الحماية الصريحة بـ`require_institutional_permission` ظاهرة لمسارات POS المالية فقط. `create_prescription` يقبل `prescriber_id` من العميل، والخدمة تنشئ الوصفة وتضع `lab_id` إذا وجد دون إثبات أن prescriber_id يساوي الطبيب الحالي أو أن الدور يسمح بالوصف.

`status` و`renew` و`cancel` و`add item` و`substitute` endpoints متاحة للمصادق عليه، وتظهر في `PharmacyService` انتقالات مباشرة دون state machine سريرية كاملة. `substitute_prescription_item` يبحث عن item باستخدام `item_id` و`rx_id` ثم يغير الدواء؛ لا يظهر في الكود المقروء تحقق واضح من `substitution_allowed` أو سبب الاستبدال أو موافقة الصيدلي أو owner scope على مستوى item.

**الإصلاح:** فصل prescriber عن pharmacist عن dispenser، فرض `prescriber_id` من actor server-side، إضافة diagnosis/encounter/consent policy، state machine، dual control للاستبدال والصرف، reason/approval audit، وتحديث سجل المواطن فقط بعد dispense مؤكد.

### C-06 — Patient Management Workspace تجريبي لكنه يظهر كأنه تشغيل فعلي

**الخطورة:** متوسطة تشغيلية وأمنية.

`PatientManagementWorkspacePage` يحتوي مرضى ومواعيد وقائمة انتظار hard-coded، ويتيح إنشاء ملف تجريبي محلياً. الصفحة تذكر ذلك بوضوح داخل بطاقة التحذير، لكن route متاح تحت `readonlyRoles` وواجهة المستخدم تشبه نظام تشغيل حقيقياً.

**الخطر:** التباس قرار الطبيب، خاصة عند اعتقاد الموظف أن التسجيل أو الموعد دخل قاعدة البيانات، ثم عدم ظهوره للمواطن أو للمختبر أو للصيدلية.

**الإصلاح:** وضع وسم prototype في عنوان route نفسه، تعطيل التسجيل المحلي في production builds، وإظهار رابط واضح إلى contract readiness بدلاً من زر يبدو تشغيلياً.

### C-07 — عدم اكتمال دورة Patient Visit وEncounter

**الخطورة:** عائق تشغيلي عالٍ، وليس ثغرة كشف بحد ذاته.

صفحة الجاهزية تصنف Check-in وQueue وEncounter وpatient view كـ`BACKEND_DEPENDENCY`، وTriage وEncounter-linked results وClose Encounter كـ`BLOCKED`. لا توجد بيانات أو mutations أو عقد تشغيلية في هذه الصفحة.

**الأثر:** لا توجد نقطة server-confirmed تربط الموعد بالوصول، ولا مكان موحد للتاريخ السريري، ولا مراجعة نتيجة، ولا إغلاق زيارة أو Visit Summary.

**الإصلاح:** تنفيذ العقود بالترتيب: check-in، queue، encounter، triage، documentation، orders/results review، close encounter، summary. كل انتقال يحتاج actor/workspace، version، idempotency، audit، واختبارات انتقال سلبية.

### C-08 — فجوة أدوار بين frontend RoleGuard وbackend authorization

**الخطورة:** متوسطة إلى عالية.

`readonlyRoles` تشمل `doctor` و`staff` و`lab_staff` و`demo_viewer` وتفتح `/clinical-workspace` و`patient-management` و`pharmacy-operations` و`billing-insurance`. هذا حارس عرض، وليس قراراً خادمياً. في المقابل، بعض backend legacy endpoints تعتمد `get_current_user` فقط وبعضها لا يتطابق مع `permissions/index.ts`.

**الأثر:** الدور قد يرى شاشة لا يستطيع تشغيلها، أو قد يصل مباشرة إلى endpoint legacy لا يفترض أن الشاشة الحديثة تستخدمه، أو قد يمنع canonical gateway الطبيب بسبب mapping قديم رغم أن frontend سمح له.

**الإصلاح:** إنشاء `doctor.read` و`doctor.write` و`pharmacist.dispense` و`lab.validate` و`institution.audit` كقرارات server-side قابلة للتدقيق، ثم توليد navigation من capability response خادمي لا من role names ثابتة فقط.

### C-09 — ازدواجية canonical وlegacy surfaces

**الخطورة:** عالية من ناحية الاتساق والتعرض.

يوجد `/api/v1/clinical` canonical، و`/clinical`، و`/clinical/orders`، و`/clinical/documentation`، و`/results` frontend bridge، و`/patient-card`، وclients عامة في `endpoints.ts`. الواجهة الحديثة تمنع بعض direct REST، لكن وجود clients ومسارات مسجلة يزيد احتمال أن يعاد استخدام endpoint قديم أو أن تختلف حالة الطلب والنتيجة بين مصدرين.

**الإصلاح:** إعداد inventory نهائي، تعيين owner وعقد لكل route، تعطيل غير المستخدم بـ410، ومنع import من `endpoints.ts` للمجالات السريرية legacy عبر lint rule أو boundary test.

### C-10 — الإحالات والمواعيد بلا رحلة طبيب canonical موحدة مثبتة

**الخطورة:** متوسطة إلى عالية تشغيلية.

المستودع يحتوي نماذج citizen وnational وradiology وcare-continuum ومواعيد متعددة. المسار المواطن محروس بعلاقة citizen في `/citizen-platform`، لكن هذا لا يثبت وجود مسار الطبيب من إنشاء referral/appointment إلى قبول الوجهة والتحديث والتوثيق والإغلاق داخل نفس workspace. النماذج المتعددة تعني تقاطعاً محتملاً بين `patient_id` و`citizen_id` و`practitioner_id` و`facility_id` دون عقد طبيب موحد مثبت.

**الإصلاح:** اختيار canonical Referral وAppointment وEncounter contracts، ثم إنشاء cross-organization consent/acceptance workflow وعدم السماح بتغيير الحالة من client body فقط.

### C-11 — فجوة review/approve للنتائج

**الخطورة:** عالية تشغيلية.

`results.read` يثبت القراءة الآمنة لنتائج الطلب، لكنه لا يوفر للطبيب review، acknowledgment، correction، validation، أو escalation. `/results` القديم لا يعوض ذلك لأنه bridge فقط. عرض نتيجة غير مساوٍ لاعتمادها سريرياً.

**الإصلاح:** بناء `results.review` و`results.validate` منفصلين، مع role/department policy، version conflict، actor attribution، audit immutable، وعدم تعديل القيمة الأصلية من الواجهة.

## 4. التقاطعات والتناقضات الرئيسية

| رقم | التقاطع أو التناقض | دليل المصدر | أثره |
|---|---|---|---|
| X-01 | الواجهة الحديثة تقول قراءة محكومة، بينما legacy documentation/orders تملك writes | [2] [6] [7] | مساران لقرار سريري واحد |
| X-02 | `/results` لا يعرض شيئاً، بينما Clinical Workspace يعرض results.read | [16] [2] | UX confusion وroute drift |
| X-03 | canonical DTO يمنع phone/health_id، بينما patient-card يعرضهما ويعيد token | [3] [10] [11] | اختلاف مستوى كشف البيانات |
| X-04 | `readonlyRoles` تفتح pharmacy/billing/device surfaces، بينما backend operations لها صلاحيات مختلفة | [1] [12] | parity gap وحقول واجهة مضللة |
| X-05 | doctor/staff/lab_staff/demo_viewer في قائمة واحدة | [1] | لا يوجد فصل واضح بين طبيب ومختبري ومراقب تجريبي |
| X-06 | `patient_id` و`encounter_id` و`provider_id` تأتي من client في عدة legacy payloads | [6] [7] [12] | خطر انتحال نسبة العملية لمريض/provider آخر |
| X-07 | بيانات patient management محلية، بينما patient-card وpatients حقيقية | [14] [10] | خلط prototype مع production |
| X-08 | legacy stores in-memory، canonical reads DB-backed | [6] [7] [4] | عدم اتساق وفقدان بيانات |
| X-09 | مسار المواطن محروس بعلاقة، لكن مسار الطبيب لا يملك relationship/assignment واضحاً لكل مريض | [citizen routes](https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/citizen_platform/routes.py) [5] | ضعف مبدأ minimum necessary access |
| X-10 | نتائج المختبر قابلة للعرض لكن لا يوجد close encounter أو review/approve | [2] [15] [16] | لا توجد مسؤولية سريرية نهائية |

## 5. ما تم إثباته بالاختبارات وما لم يُثبت

| الفئة | النتيجة | حدود الدليل |
|---|---|---|
| Clinical Gateway contracts/service | 12 اختباراً سابقاً ناجحاً، وتدخل ضمن 29 اختبار backend الحالي | تثبت contract/context logic، لا تثبت كل route legacy |
| Patient Card | 15 اختباراً ضمن دفعة patient-card ناجحة | تثبت lab isolation وHMAC وaudit لـadmin lab users؛ لا تثبت doctor/citizen role matrix كاملة |
| Pharmacy POS | اختباران ناجحان ضمن الدفعة الحالية | لا يغطيان prescription prescriber proof أو substitution policy كاملة |
| Frontend workspace/barriers | 70 اختباراً ناجحاً | تثبت parser وread barrier وبعض readiness، لا E2E مع session/workspace حقيقي |
| Legacy clinical documentation/orders | لا توجد اختبارات backend مطابقة في `backend/tests` | هذه فجوة اختبارية مستقلة، وليست دليلاً على أمانها |
| Native parity | غير مثبتة على current head | Flutter/native CI وreal-device evidence غير متاحين |

تم تشغيل الدفعة الحالية محلياً: **29 اختبار backend ناجحاً** في clinical gateway وpatient-card وpharmacy POS، و**70 اختبار frontend ناجحاً** في readiness وworkspace barriers. توجد تحذيرات بيئية غير حاجبة في pytest. لم تُعتبر الملاحظات source-confirmed أعلاه اختراقاً runtime مثبتاً ما لم يذكر خلاف ذلك؛ يلزم negative test مخصص قبل الإغلاق.

## 6. خطة الإصلاح ذات الأولوية

### P0 — احتواء فوري قبل أي توسعة

يجب تعطيل أو حجب مسارات `/clinical/documentation` و`/clinical/orders` الكتابية، ومسارات الكتابة الحساسة في `/clinical`، إلى أن تُربط بقرار actor/workspace/tenant. يجب منع استعمال global in-memory stores في أي مسار يحمل بيانات أو قراراً سريرياً. كما يجب إضافة deny tests تتأكد من رفض user من مختبر آخر، ورفض staff/lab staff غير المصرح، ورفض تغيير `patient_id` أو `provider_id` من payload.

في الوقت نفسه يجب جعل `/patient-card` institutional/workspace-aware، وإيقاف إعادة `token` في JSON، ومراجعة صلاحيات الطباعة والتاريخ. كل فشل في هذه الاختبارات يبقي P4 في SAFE_STOP.

### P1 — توحيد هوية الطبيب والموارد

يجب إنشاء Doctor Clinical Actor Context واحد يربط account وidentity وmembership وorganization وfacility وworkspace وdepartment وprovider registry. لا يجوز أن يكون `prescriber_id` أو `ordering_provider_id` سلطة يرسلها العميل؛ يرسل العميل intent فقط، ويستنتج الخادم actor الحقيقي.

بعد ذلك تُنقل documentation وorders وencounters إلى عقود canonical durable، مع optimistic locking وidempotency وimmutable audit وstate machine لكل مورد.

### P1 — تنفيذ دورة الطبيب الأساسية

الترتيب الآمن هو: فتح مساحة العمل، patient search policy، appointment/check-in، queue، encounter، triage، SOAP/progress note، order، result ingestion، result review، prescription، referral، close encounter، Visit Summary. كل خطوة تحتاج contract typed واختبارات success/deny/tenant mismatch/session expiry/duplicate retry.

### P2 — الوصفات والإحالات والتشغيل البيني

يجب فصل صلاحيات الطبيب والصيدلي والمختبري، وإضافة dual control للاستبدال والصرف، وتسجيل سبب وبديل العلاج وسجل المواطن بعد صرف مؤكد. كما يجب اعتماد Referral وAppointment canonical واحدين مع consent/acceptance عند عبور المؤسسات.

### P2 — التكافؤ عبر المنصات

لا يُعلن اكتمال مسار الطبيب قبل تنفيذ نفس negative authorization matrix في Web/PWA وAndroid وiOS وDesktop، وتشغيل native CI على current head، وإثبات session expiry وtenant mismatch وoffline-safe behavior وعدم وجود fallback إلى routes legacy.

## 7. قرار الجاهزية

| القرار | الحالة |
|---|---|
| Clinical read gateway | PASS محلياً للعقود والاختبارات |
| Full doctor workflow | NOT_BUILT / PARTIAL |
| Legacy clinical writes | SECURITY BLOCKED حتى الاحتواء |
| Patient Visit / Encounter | BLOCKED |
| Prescription governance | PARTIAL / HIGH RISK |
| Native parity | UNVERIFIED |
| Android signing incident | SECURITY BLOCKED |
| P4 | PARTIAL / SECURITY_BLOCKED |
| P5 | BLOCKED |

> **الخلاصة:** المنصة تملك الآن نواة قراءة سريرية محكومة، لكنها لا تملك بعد مسار طبيب تشغيلياً كاملاً وآمناً من الدخول إلى إغلاق الزيارة. الأولوية ليست إضافة شاشات جديدة، بل إزالة المسارات المتناقضة، احتواء legacy writes، توحيد actor/workspace authorization، ثم بناء Encounter وdocumentation وorders وprescriptions على نفس البوابة الخادمية.

## المراجع

[1]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/frontend-v3/src/routes/index.tsx "React routes and RoleGuard definitions"
[2]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/frontend-v3/src/pages/clinical/ClinicalWorkspacePage.tsx "Clinical Workspace"
[3]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/frontend-v3/src/api/workspaceScopedReads.ts "Canonical workspace-scoped read client"
[4]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/clinical_gateway/routes.py "Canonical Clinical Read Gateway routes"
[5]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/clinical_gateway/context.py "Clinical Gateway Context Resolver"
[6]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/routes/clinical_documentation.py "Legacy clinical documentation routes"
[7]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/routes/clinical_orders.py "Legacy clinical order routes"
[8]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/routes/clinical.py "Clinical terminology, knowledge, CDS and quality routes"
[9]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/security/dependencies.py "Authentication and permission dependencies"
[10]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/frontend-v3/src/pages/patient-card/PatientCardPage.tsx "Legacy Patient Card UI"
[11]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/routes/patient_card.py "Patient Card backend routes"
[12]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/pharmacy/routes.py "Pharmacy and prescription routes"
[13]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/pharmacy/services.py "Pharmacy service prescription workflow"
[14]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/frontend-v3/src/pages/patients/PatientManagementWorkspacePage.tsx "Synthetic Patient Management Workspace"
[15]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/frontend-v3/src/pages/patient-visit/PatientVisitReadinessPage.tsx "Patient Visit readiness and blockers"
[16]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/frontend-v3/src/pages/results/ResultsPage.tsx "Legacy Results bridge"
[17]: https://github.com/samertts/gula-platform/blob/chore/security-ddos-hardening-clean/backend/app/citizen_platform/routes.py "Citizen relationship-scoped routes"
