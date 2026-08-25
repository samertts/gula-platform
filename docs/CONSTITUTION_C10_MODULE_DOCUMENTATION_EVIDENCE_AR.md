# دليل C10: توثيق الوحدات الحرجة في الخلفية

**الفرع:** `docs/c10-critical-module-readmes`
**التزام التنفيذ:** `54417ddf`
**الحالة:** تحسن موضعي قابل للقياس؛ C10 والإطلاق ما زالا **مفتوحين / NO-GO**.

## الجرد

يحتوي `backend/app` في RC1 على 355 دليلاً به `__init__.py`، وكان 18 منها فقط يملك `README.md` محلياً. لا تمثل كل هذه الأدلة حدوداً مستقلة متساوية؛ فبعضها commands/events/queries/tests داخل حزمة أكبر. لذلك لا يصح توليد مئات ملفات README شكلية أو الادعاء بأن كل package موثق بهذه الدفعة.

## المعالجة المنفذة

أضيف README إلى أربع وحدات ذات أهمية عالية ولم يكن لها توثيق محلي:

| الحزمة | موضوع README | الضابط الموثق |
|---|---|---|
| `app/clinical` | حارس الأوامر والحالات والتدقيق | لا bypass للأمر السريري أو آلة الحالة. |
| `app/clinical_gateway` | عقود القراءة والسياق | لا كتابة سريرية أو تجاوز للعزل. |
| `app/devices` | الحجر والهوية والمراجعة | default-deny؛ لا نتيجة أو إطلاق من جهاز. |
| `app/fhir` | القدرات وFHIR R4 والتبادل | العزل والحارس السريري لا يلغيهما التكامل. |

لم يتغير أي ملف Python أو endpoint أو schema أو migration أو feature flag. وفحص Git أكد وجود الملفات الأربعة وعناوينها ومرور `git diff --check` قبل الالتزام.

## ما يبقي C10 مفتوحاً

يحتاج C10 إلى جرد architecture-bounded للموديولات، ثم owner لكل موديول وتعريف أدنى لمحتوى README، وربما حارس non-regression بعد اعتماد baseline. كما يحتاج توثيق الوحدات المتبقية على دفعات موضوعية لا على أساس كل `__init__.py` آلياً. لا تخفض هذه الدفعة أي معيار ولا تمنح قرار GO.

## المراجع

[1] [تقرير التحقق الدستوري: C10](constitution/CONSTITUTION-VALIDATION-REPORT.md)

[2] [README وحدة Clinical](../backend/app/clinical/README.md)

[3] [README وحدة Device Integration](../backend/app/devices/README.md)

[4] [README وحدة FHIR](../backend/app/fhir/README.md)
