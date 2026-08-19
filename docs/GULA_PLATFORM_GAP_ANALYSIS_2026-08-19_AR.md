# تحليل فجوات خدمات ومنصة GULA

**تاريخ التحليل:** 19 أغسطس 2026

**نطاق التحليل:** مراجعة بنية المستودع، وحدات الخدمات، مسارات التكامل، سطح FHIR، أدلة الجاهزية، ومصفوفة الفجوات الحالية. لا يُعد هذا التحليل تدقيقاً طبياً أو قانونياً أو شهادة جاهزية للإنتاج.

## الخلاصة التنفيذية

يمتلك GULA أساساً قوياً لمنصة مختبرات وصحة رقمية متعددة المستأجرين، يتضمن خدمات المرضى والطلبات والنتائج والعينات، طبقات RBAC/ABAC والموافقة والتدقيق، تكاملات FHIR وHL7 جزئية، محرك قواعد عام، بنية إشعارات وجدولة، وطبقات اختبار وأمن وتعافٍ موثقة. لذلك فإن النقص الأكبر ليس في إضافة مزيد من الوثائق، بل في تحويل القدرات العامة أو الجزئية إلى **خدمات سريرية تشغيلية مكتملة ومثبتة**.

أهم ما ينقص المنصة حتى تصبح منصة رعاية مزمنة متكاملة هو: طبقة استقبال حقيقية للأجهزة القابلة للارتداء، مخزن قياسات حيوية موحّد، خدمة خطوط أساسية شخصية مُدارة دورة حياتها، مسار تنبيهات سريري متدرج مع إزالة التكرار والتصعيد، إدارة برنامج رعاية مزمنة، واجهة طبيب تشغيلية، طبقة فيديو/تطبيب عن بُعد، تكاملات صيدلية ومواعيد ومطالبات عند الحاجة، واستكمال أدلة التشغيل والامتثال. كما توجد مخاطر حالية يجب إغلاقها قبل أي توسع: CAS لنتائج المختبر، HA فعلي لـRedis، إثبات الاستعادة وRTO/RPO، اختبارات PostgreSQL/Redis الحية، واستكمال فجوات الخصوصية والإصدارات القانونية.

> **قاعدة التصنيف:** «مفقود» يعني عدم العثور على خدمة إنتاجية متكاملة في المسح؛ «جزئي» يعني وجود أساس أو وحدة أولية دون إثبات تشغيلي أو دون دورة كاملة؛ «غير مثبت» يعني وجود كود أو وثيقة لكن دون اختبار حي أو دليل قابل لإعادة الإنتاج. لا يجوز تفسير «غير مذكور» على أنه «غير موجود» دون مراجعة مالك المجال.

## 1. ما هو موجود حالياً

| المجال | الدليل داخل المستودع | التقييم |
|---|---|---|
| المختبر وإدارة النتائج | خدمات المرضى والطلبات والنتائج والعينات، وحالات سير عمل للنتائج | أساس تشغيلي قوي؛ CAS لنتائج `LabResult` ما يزال مخاطرة موثقة |
| القواعد السريرية العامة | `backend/app/national/rules_engine/` يحتوي تعريف القواعد، الإصدارات، التفعيل، المحاكاة، والتقييم | موجود كإطار عام، وليس محرك رعاية مزمنة كاملاً |
| interoperability | FHIR R4 وHL7 ومحوّلات ومصطلحات | تغطية FHIR المعلنة 16 نوعاً منفذاً، و`Procedure` و`Bundle` كـStub، و`Goal` و`Device` و`Location` و`Provenance` مخططة [1] |
| الهوية والصلاحيات | JWT/RBAC/ABAC/MFA/SAML/OAuth، عزل المستأجر، consent، وسجل تدقيق hash chain | واسع ومهم، لكن يحتاج تحقق تشغيلـي وإغلاق فجوات الجاهزية الحالية |
| الإشعارات والجدولة | `notification_platform` و`scheduling_platform` داخل المجال الوطني، وخدمة إشعارات مرتبطة بمحرك القواعد | أساس موجود؛ لا يوجد دليل كافٍ على دورة تنبيه سريري متدرجة ومجمّعة مع قنوات إنتاجية متعددة |
| التكاملات الخارجية الحالية | بوابات الهوية الوطنية والتأمين والإقامة وCloudflare؛ الوضع الافتراضي Stub وفق الدليل | لا يوجد في دليل التكاملات الحالي محول إنتاجي واضح لـApple Health/HealthKit أو Fitbit أو Garmin أو Dexcom |
| الاستمرارية والمراقبة | Prometheus/health checks/backup scripts/chaos tests وأدلة DR | الأدوات موجودة، لكن الاستعادة الحقيقية وRTO/RPO والـsynthetic monitoring ما زالت بوابات تشغيلية غير مكتملة |

## 2. الخدمات الناقصة أو غير المكتملة ذات الأولوية

### 2.1 طبقة الأجهزة القابلة للارتداء واستقبال القياسات

لا يظهر في دليل التكاملات الحالي أو مسارات الخدمات محول مكتمل لـApple Health/HealthKit أو Fitbit أو Garmin أو Dexcom أو أجهزة ضغط/أكسجة قابلة للارتداء. توجد طبقات عامة للتكامل، لكن `MQTTGateway.receive()` يعيد `None`، وغياب مكتبة MQTT يحول الاتصال إلى وضع محاكاة مع اعتبار الاتصال ناجحاً؛ وهذا لا يساوي قناة استقبال سريرية حقيقية [2].

**الخدمة المطلوبة:** `Wearable Ingestion Service` تشمل OAuth/device pairing، webhooks أو polling موثوق، التحقق من توقيع المصدر، إزالة التكرار، ترتيب الأحداث، معالجة التأخر، جودة الإشارة، قاموس وحدات، وتخزين raw/normalized مع tenant وpatient binding.

**شروط القبول:** لا تُقبل قراءة دون مصدر موثق ووقت قياس ووحدة وجودة إشارة؛ كل رسالة تحمل idempotency key؛ فشل التحقق لا يصل لمحرك القرار؛ وتوجد replay/duplicate/out-of-order tests.

### 2.2 نموذج بيانات القياسات الحيوية الموحد

توجد موارد FHIR عامة، لكن لا يظهر دليل على مخزن متخصص لسلاسل القياسات الزمنية مع provenance وجودة إشارة وتواتر وعتبات شخصية. وجود `Observation` في FHIR لا يثبت وحده وجود pipeline مناسب لآلاف القراءات اليومية أو retention/partitioning أو reconciliation.

**الخدمة المطلوبة:** `Vital Signs/Observation Store` يدعم FHIR Observation وDevice وProvenance، raw immutable events، normalized observations، units UCUM، device calibration metadata، clock skew، late arrivals، retention، وtenant-scoped queries.

### 2.3 إدارة الخط الأساسي الشخصي والنماذج

لا تظهر خدمة إنتاجية منفصلة لإدارة دورة حياة `AI Baseline` لكل مريض، ولا registry واضح للنموذج والإصدار وبيانات التدريب والموافقة وdrift والتقييم والتحيز. وجود وحدات AI أو كشف شذوذ عام لا يثبت نموذجاً شخصياً آمناً للاستخدام السريري.

**الخدمة المطلوبة:** `Personal Baseline Service` مع cold-start policy، نافذة تعلم، استبعاد فترات المرض الحاد، versioned model registry، feature provenance، confidence، drift monitoring، clinician override، rollback، ومخرجات display-only إلى أن يعتمد المسار السريري.

**قيد سلامة:** لا يجوز للخوارزمية أن تغيّر علاجاً أو جرعة أو حالة مريض تلقائياً. تقتصر مخرجاتها أولاً على دعم القرار مع تفسير وإظهار جودة البيانات ومصدرها.

### 2.4 محرك التنبيهات السريرية المتدرج

محرك القواعد الحالي يقيّم القواعد النشطة ويرسل إشعاراً عند المخالفة، لكنه لا يثبت وجود alert deduplication، suppression window، correlation بين عدة حساسات، personal baseline comparison، quiet hours، acknowledgement SLA، escalation ladder، أو closed-loop outcome. كما أن `get_evaluation_history()` في خدمة القواعد يعيد قائمة فارغة، ويستخدم اختيار القواعد النشطة العام دون دليل على تصفية سريرية حسب patient/condition/tenant في مسار `find_active()` [3]. هذه نقطة تحتاج مراجعة سريرية وأمنية قبل ربطها ببيانات حقيقية.

**الخدمة المطلوبة:** `Clinical Alert Orchestrator` يفصل بين event، signal، alert، case، وescalation؛ يطبق SQI وcross-sensor validation وrate limits والتجميع والتصعيد إلى المريض ثم المدرب ثم الطبيب؛ يحتفظ بسبب القرار، الإصدار، الثقة، acknowledgement، disposition، وaudit trail.

### 2.5 برنامج إدارة الأمراض المزمنة

لا يظهر نطاق مكتمل يجمع registry للمرضى، risk stratification، care plan زمني، أهدافاً، مهاماً للمريض، مراجعات دورية، قياسات منزلية، adherence، مدرباً صحياً، تعليمات، escalation، ومخرجات outcome. وجود `CarePlan` في FHIR أو workflow عام لا يساوي برنامجاً للسكري أو ارتفاع الضغط أو قصور القلب.

**الخدمة المطلوبة:** `Chronic Care Program Service` يبدأ بنطاق محدود مثل السكري وارتفاع الضغط، مع قوالب بروتوكولات versioned، care team assignment، patient-reported outcomes، medication reconciliation، schedule، education، وقيود صريحة تمنع التشخيص أو تغيير العلاج بلا قرار بشري مخول.

### 2.6 واجهة الطبيب وسطح إدارة الحالات

توجد مكونات Frontend وتقارير ولوحات، لكن لا يوجد في المسح دليل كافٍ على شاشة تشغيلية متخصصة تعرض work queue للأطباء، تلخيصاً شخصياً، timeline، trend مقابل baseline، سبب التنبيه، جودة الإشارة، الإجراءات المقترحة، وprogressive disclosure. كما أن `docs/DEPLOYMENT_READINESS.md` يذكر أن بعض صفحات UI الخاصة بالنتائج وإدارة الأجهزة ما زالت ضمن خارطة الطريق [4].

**الخدمة المطلوبة:** `Clinician Chronic Care Dashboard` مع patient list مرتبة بالخطورة، alert/case inbox، triage، trend charts، explanation drawer، acknowledgment/disposition، care plan، audit، وواجهة offline/degraded لا تسمح بكتابة سريرية غير قابلة للتسوية.

### 2.7 التطبيب عن بُعد والاتصال المرئي

لا يوجد دليل واضح على خدمة WebRTC/telehealth إنتاجية تشمل إنشاء الجلسة، consent، waiting room، identity verification، recording policy، clinical note، billing، وخطة بديلة عند فشل الفيديو. ينبغي اعتبارها خدمة مفقودة حتى تثبت خريطة routes وprovider وtests وrunbook.

**الخدمة المطلوبة:** `Telehealth Session Service` مع provider abstraction، short-lived session tokens، تشفير، عدم تسجيل افتراضي، موافقة صريحة، audit، fallback صوتي/هاتفـي، وربط encounter بالمريض والطبيب.

### 2.8 تكاملات الصيدلية والمواعيد والمطالبات

توجد بوابات تأمين وجدولة أو POS في المستودع، لكن التكاملات التشغيلية الكاملة مع صيدليات، e-prescribing، formulary، medication adherence، شركات التأمين، المطالبات، وإعادة الإحالة ليست مثبتة كمسارات end-to-end. يجب عدم اعتبار وجود نموذج أو route عاماً دليلاً على تكامل حي.

**الخدمة المطلوبة حسب نموذج العمل:** pharmacy/e-prescribing adapter، claims/eligibility service، referral service، وappointment provider adapter؛ وكلها تبدأ Stub/Shadow وتنتقل إلى Live بعد اختبار العقد، الصلاحيات، الإعادة الآمنة، والـaudit.

## 3. مخاطر قائمة يجب إغلاقها قبل التوسع

| الأولوية | الفجوة الحالية | الأثر | معيار الإغلاق |
|---|---|---|---|
| P0 | سلسلة Alembic وDHIS2 وقرائن PostgreSQL | فشل نشر أو endpoint تقارير 5xx | fresh PostgreSQL upgrade/round-trip وquery/auth tests |
| P1 | `LabResult.version` موجود لكن CAS غير مفروض على مسارات mutation | overwrite صامت لنتيجة مخبرية | stale write يعيد 409، لا overwrite، مع audit violation |
| P1 | Redis HA والمشاركة بين workers غير مثبتة في نشر حي | rate limit/revocation/session inconsistency | multi-worker test وRedis outage drill وmetrics |
| P1 | idempotency ليست مغطاة لكل critical POST | تكرار order/result/claim بعد retry | same key يعيد نفس النتيجة، payload مختلف يعيد 409 |
| P1 | backup/restore وRTO/RPO غير مثبتة عملياً | فقدان بيانات أو توقف طويل | restore من backup حقيقي، checksum، audit-chain verification، زمن مسجل |
| P2 | offline-first capture/sync وconflict resolution غير مثبتة | overwrite أو duplicate عند انقطاع الشبكة | encrypted local queue، reconciliation، conflict workflow، E2E |
| P2 | الأداء مثبت محلياً فقط | فشل SLA في PostgreSQL/Redis الإنتاجي | load/soak/stress test مع p50/p95/p99 وerror rate |
| P2 | runbooks التشغيلية غير مادية بالكامل | بطء الاستجابة للحوادث | إنشاء `docs/runbooks/*.md` وتمرينها دورياً |
| P3 | WebAuthn/Passkeys غير منفذة | MFA أقل قوة للفئات الحساسة | threat model، recovery abuse tests، rollout تدريجي |
| P3 | legal/privacy versioning جزئي | موافقة أو احتفاظ أو طلبات أصحاب البيانات غير مكتملة | consent/version/retention/DSAR tests ومراجعة قانونية |

تستند هذه القائمة إلى `GULA_GAP_MATRIX.md` و`docs/DEPLOYMENT_READINESS.md`، اللذين يميزان بين `IMPLEMENTED` و`PARTIAL` و`PROPOSED` و`NOT VERIFIED`، ولا ينبغي تجاوز تصنيفهما بعبارات عامة عن الجاهزية [5] [6].

## 4. ترتيب التنفيذ المقترح

### المرحلة الأولى: تثبيت السلامة والبيانات

تبدأ المرحلة بإغلاق مخاطر PostgreSQL وAlembic وDHIS2، فرض CAS على النتائج، توحيد idempotency، تثبيت Redis المشترك، وإكمال restore drill. لا تُفتح بيانات الأجهزة أو قواعد سريرية شخصية قبل نجاح هذه البوابة.

### المرحلة الثانية: تأسيس خط القياسات

ينفذ الفريق `Wearable Ingestion Service` و`Vital Signs Store` وFHIR Device/Provenance، مع مزود واحد قابل للاختبار أولاً. تُحفظ البيانات الخام بصورة غير قابلة للتعديل، وتُنتج نسخة normalized versioned، ويُفصل ingestion عن decisioning.

### المرحلة الثالثة: رعاية مزمنة محدودة النطاق

يُختار مرض واحد أو اثنان، وتُبنى care pathways versioned وclinical review board. يبدأ baseline display-only، ثم alert orchestrator بعتبات محافظة وclosed-loop review. لا يوجد autonomous treatment.

### المرحلة الرابعة: تجربة الطبيب والاتصالات

يُبنى dashboard بمبدأ الإفصاح التدريجي، ثم telehealth أو notification channels وفق الأولوية التجارية والتنظيمية. تُقاس alert burden وtime-to-acknowledge وfalse-positive rate وclinician override.

### المرحلة الخامسة: التوسع والتكاملات

بعد نجاح pilot، تُضاف مزودات الأجهزة والتأمين والصيدلة، وتُراجع اتفاقيات معالجة البيانات، وتُنفذ اختبارات multi-tenant/load/DR في بيئة مماثلة للإنتاج.

## 5. قرار جاهزية مقترح

| القرار | الحالة الحالية |
|---|---|
| تشغيل GULA كمنصة مختبرات متعددة المستأجرين في Pilot محدود | ممكن فقط بعد إغلاق بوابات P0 ونتائج staging المطلوبة |
| تشغيل مراقبة Wearables سريرية لحظية | غير جاهز؛ طبقة ingestion والبيانات والتنبيهات تحتاج بناء وإثبات |
| تشغيل AI Baselines لاتخاذ قرار علاجي آلي | غير مقبول؛ يجب أن تبقى المخرجات display-only مع مراجعة بشرية |
| إعلان HIPAA/GDPR/PDPL compliance | غير جائز من الأدلة البرمجية وحدها؛ يلزم نطاق قانوني ومراجعة مستقلة واتفاقيات وضوابط تشغيلية |
| اعتماد Warm Standby | ممكن كقرار استمرارية، لكن بعد restore drill وقياس RTO/RPO الفعليين |

## 6. ملاحظات على الوثائق المرفوعة

الوثائق المرفوعة في `docs/gula-strategies/` تمثل تصاميم وخططاً للاستفادة منها، وليست دليلاً على أن كل خدمة ذُكرت فيها موجودة في الكود. يجب ربط كل وثيقة بتذكرة، مالك، ADR، عقد API، schema، اختبارات، runbook، وموافقة سريرية/أمنية عند اللزوم. ويظل `docs/INTEGRATIONS.md` مرجعاً مهماً لأن التكاملات الخارجية تعمل Stub افتراضياً، ولا تنتقل إلى Live إلا ببيانات اعتماد وضبط صريح [7].

## المراجع

[1]: ../backend/app/fhir/_reference.py "FHIR resource coverage registry in GULA"

[2]: ../backend/app/integration/gateway/mqtt_gateway.py "MQTT gateway implementation"

[3]: ../backend/app/national/rules_engine/application/service.py "Rules engine application service"

[4]: DEPLOYMENT_READINESS.md "National-Scale Deployment Readiness"

[5]: ../GULA_GAP_MATRIX.md "GULA Gap Matrix"

[6]: DEPLOYMENT_READINESS.md "Deployment readiness checklist and unresolved-risk register"

[7]: INTEGRATIONS.md "GULA Integrations Guide"

[8]: ../backend/app/integration/connector/dicom.py "DICOM connector implementation"

[9]: ../backend/app/national/notification_platform/ "Notification platform package"

[10]: ../backend/app/national/scheduling_platform/ "Scheduling platform package"
