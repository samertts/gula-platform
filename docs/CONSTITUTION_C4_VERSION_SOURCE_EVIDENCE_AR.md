# دليل C4: مصدر موحّد لنسخة المنصة التشغيلية

**الفرع:** `fix/version-source-consistency`
**التزام التنفيذ:** `e16c63acc286d175e3e201bbb6211d116f68dffd`
**الحالة:** خُفّض عدم اتساق metadata التشغيلية؛ يبقى C4 **مفتوحاً / NO-GO** إلى جرد الوثائق والتغليف والإصدارات التاريخية واعتماد مصدر النسخة وحوكمته.

> هذه الدفعة لا تغيّر إصدار FHIR R4 (`4.0.1`) أو إصدارات عقود الأحداث أو إصدارات نماذج الأشعة أو API path versions. كما لا تغيّر قاعدة بيانات أو بيانات سريرية أو سلوك أمر سريري.

## الخطر المعالج

أظهر الجرد أن `APP_VERSION` و`pyproject.toml` يحددان نسخة المنصة `2.5.0`، بينما كانت عدة مخرجات تشغيلية ووثائق machine-readable تعرض `2.1.0` بصورة ثابتة. يسبب ذلك التباساً في التشخيص، وبيانات قدرة FHIR، ووثيقة AsyncAPI، وmetadata الـSBOM، وتعريف Kernel. يسجل تقرير التحقق C4 تعارض النسخة، لكن أمثلته التاريخية لا تمثل جرد RC1 الحالي؛ لذا لا تعدّل هذه الدفعة التقرير أو تدّعي حله. [1]

## الضابط المضاف

| الموضع | التغيير | ما لم يتغير |
|---|---|---|
| `ai_fabric/routes.py` | health metadata تستخدم `APP_VERSION` | الصلاحيات ومكونات SDK وإجابات AI |
| `contracts/events.py` | `info.version` في AsyncAPI تستخدم `APP_VERSION` | event registry وإصدارات الأحداث الفردية |
| `engineering/security/sbom.py` | metadata أداة SBOM تستخدم `APP_VERSION` وUTC واعياً بالمنطقة الزمنية | تحليل dependencies وصيغة CycloneDX |
| `fhir/_capabilities.py` | software version تستخدم `APP_VERSION` | `fhirVersion` وموارد FHIR والـprofiles |
| `kernel/integration.py` | default Kernel version يستخدم `APP_VERSION` مع بقاء override البيئة | إعدادات Kernel الأخرى |
| `knowledge_graph/fhir_catalog.py` | CapabilityStatement المتولد يستخدم `APP_VERSION` | FHIR version وكتالوج الموارد |

اختبارات C4 تثبت أن AsyncAPI وبياني FHIR وmetadata مولد SBOM ترجع النسخة المركزية، وأن Kernel يستعملها عند غياب override ويحترم override صريحاً في البيئة. [2]

## الأدلة المحلية

| التحقق | النتيجة |
|---|---|
| اختبار اتساق نسخة C4 | 3/3 ناجح. |
| انحدار FHIR الموجه مع C4 | 39/39 ناجحاً عبر comprehensive/interoperability/hardening/R4 exchange. |
| Ruff للملفات المتغيرة | ناجح. |
| MyPy للاختبار الجديد | ناجح. |
| بوابة changed-files مقابل RC1 | **PASS** عند `e16c63ac`: Ruff `0→0` وMyPy `61→61` للملفات المتغيرة؛ الدين الحرج بقي Ruff `27` وMyPy `510`. |

جرت ملاحظة تحذيري FastAPI/Starlette خارجيين في اختبار FHIR؛ لم يضف C4 تحذيرات SBOM المتقادمة بعد التحويل إلى UTC واعٍ بالمنطقة الزمنية.

## ما يبقي C4 مفتوحاً

لا يكفي توحيد ستة مخرجات تشغيلية لإغلاق سياسة الإصدار. يلزم مالك الإصدار أن يقرر مصدر الحقيقة المُلزم للتغليف وAndroid وواجهات frontend وملفات النشر، وأن يجرد كل الإشارات التاريخية بوصفها إما سياق إصدار مؤرشف أو metadata تشغيلية تستلزم التحديث. كما يلزم تنفيذ تشغيل CI خارجي على مرشح مدمج. لا يجوز تعديل manifest أو وسم release أو تقرير التحقق أو اعتبار ذلك دليلاً على GO قبل الأدلة البشرية والخارجية الأخرى.

## المراجع

[1] [تقرير التحقق الدستوري: C4](constitution/CONSTITUTION-VALIDATION-REPORT.md)

[2] [اختبار اتساق مصدر النسخة](../backend/tests/test_version_source_consistency.py)

[3] [تعريف نسخة التطبيق](../backend/app/config.py)
