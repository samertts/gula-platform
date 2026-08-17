# خطة اختبار تكامل خدمة Device Bridge مع منصة GULA

## 1. الهدف والنطاق

تختبر هذه الخطة المسار الكامل من جهاز المختبر الاصطناعي إلى خدمة `device_bridge` ثم إلى Backend في GULA. يبدأ المسار بإطار ASTM أو رسالة الجهاز، ويمر عبر التحقق من checksum، والتحليل والتطبيع والمطابقة، ثم يرسل النتيجة إلى endpoint المنصة `POST /device/results`. يقوم Backend بالتحقق من JWT ونطاق المؤسسة، ومطابقة `barcode` مع العينة داخل مختبر المستخدم، وإنشاء `LabResult`، وتحديث العينة إلى `analyzed` والطلب إلى `completed`، وإضافة سجل تدقيق.

لا تستخدم الاختبارات بيانات مرضى حقيقية أو معرفات وطنية حقيقية. كل القيم في هذه الخطة اصطناعية وموسومة بوضوح، ويجب تشغيل اختبار staging على نسخة منفصلة من قاعدة البيانات.

## 2. عقد التكامل الذي يجب تثبيته

يجب أن يرسل `device_bridge` الطلب التالي إلى Backend:

```json
{
  "barcode": "SAMPLE-DEVICE-001",
  "device_id": "CBC-01",
  "results": [
    {
      "test_name": "HEMOGLOBIN",
      "value": 13.5,
      "unit": "g/dL"
    }
  ]
}
```

يُرسل الاعتماد في ترويسة `Authorization: Bearer <access-token>`. لا يُعتبر `lab_id` القادم من العميل مصدر صلاحية؛ العزل المؤسسي يُحسم في Backend من JWT الخادمي ومطابقة العينة مع `LabOrder.lab_id`. إذا غاب `barcode` أو كانت قائمة النتائج فارغة، يجب أن يرفض العميل الإرسال محليًا ولا ينفذ طلب شبكة.

| طبقة التكامل | العقد الذي يجب التحقق منه | فشل الاختبار المتوقع |
|---|---|---|
| Parser | رفض الإطار ذي checksum غير صحيح وعدم إنشاء نتيجة | لا أثر سريري ولا إرسال |
| Normalizer | تحويل test code إلى قيمة canonical وحفظ UTC timestamp | نتيجة غير قابلة للإرسال |
| GulaClient | POST إلى `/device/results` مع barcode وdevice_id وAuthorization | retry/outbox عند فشل الشبكة |
| Backend auth | JWT صالح، مستخدم نشط، role وlab scope صحيحان | 401 عند غياب/تلف token |
| Tenant isolation | barcode لا يُبحث إلا داخل lab الخاص بالمستخدم | 404 عند محاولة مؤسسة أخرى |
| Clinical state | الانتقال `pending → completed` فقط، ورفض الطلب الملغى أو المقفل | 409 أو 423 بلا side effects |
| Audit | تسجيل actor وlab وresource وعدد النتائج بعد نجاح العملية | فشل مغلق إذا تعذر audit |
| Outbox/offline | إعادة المحاولة بانتظار bounded backoff وعدم إسقاط النتيجة | بقاء الرسالة pending أو dead-letter |

## 3. طبقات الاختبار

تُشغّل اختبارات الوحدة على parser وnormalizer وretry queue أولًا. بعدها تُشغّل contract tests باستخدام `httpx.MockTransport` للتأكد من شكل HTTP والـheaders دون الاتصال بالشبكة. ثم تُشغّل Backend HTTP integration tests باستخدام قاعدة SQLite الاختبارية وبيانات مختبر وعينة وطلب اصطناعية. وأخيرًا تُجرى اختبارات staging عبر شبكة حقيقية، مع مراقبة audit وoutbox وسجلات الخدمة.

الأوامر المحلية المعتمدة هي:

```bash
# اختبارات خدمة device_bridge المستقلة
make device-bridge-test

# اختبارات عقد Backend وdevice integration وoutbox
PYTHONPATH=backend pytest -q \
  backend/tests/test_device_bridge_integration.py \
  backend/tests/test_device_routes.py \
  backend/tests/test_device_outbox.py

# Backend suite الجذرية بعد فصل namespace الخدمة
pytest -q
```

لا تشغّل اختبارات `device_bridge` باستخدام `PYTHONPATH=backend`؛ لأن الخدمة تستخدم namespace محليًا باسم `app`، وإضافة Backend إلى المسار قد تجعل pytest يحمّل تطبيقًا غير صحيح.

## 4. سيناريوهات staging الإلزامية

يجب إنشاء مختبرين اصطناعيين، ومستخدمين نشطين، وطلبين، وعينتين مختلفتين. يرسل جهاز `CBC-SYN-001` نتيجة إلى عينة المختبر الأول باستخدام token خاص بالمختبر الأول. يجب أن تنجح العملية مرة واحدة، وأن يظهر `LabResult` واحد وأن تصبح العينة `analyzed` والطلب `completed`.

بعد ذلك تُختبر الحالات التالية:

| السيناريو | النتيجة الإلزامية |
|---|---|
| token مفقود أو منتهي | 401، بلا كتابة في قاعدة البيانات |
| barcode غير موجود | 404، بلا كتابة |
| barcode تابع لمختبر آخر | 404، بلا كشف لوجود العينة |
| sample rejected | 400، بلا نتيجة |
| order cancelled | 409، بلا نتيجة |
| order validated/locked | 423 أو 409، بلا تعديل |
| checksum غير صحيح | إسقاط الإطار وتسجيل خطأ تقني آمن بلا PHI |
| timeout أو 5xx من Backend | retry bounded ثم outbox/dead-letter وفق السياسة |
| انقطاع الاتصال بعد إرسال الطلب | اختبار idempotency قبل اعتبار النتيجة آمنة للإعادة |
| payload يتجاوز 100 نتيجة | 400، بلا كتابة جزئية |
| metadata تحتوي API token أو raw payload | 422 أو redaction، ولا يُخزّن السر أو payload الخام |

## 5. شرط idempotency والتعارضات السريرية

تُعد إعادة إرسال نفس batch اختبارًا حرجًا. لا يكفي أن يعيد Backend HTTP 200؛ يجب إثبات أن retry لا ينشئ `LabResult` مكررًا ولا يضيف side effect ثانيًا. ينبغي أن يستخدم العقد النهائي `Idempotency-Key` مشتقًا من المؤسسة والجهاز والعينة ورقم الرسالة، أو معرفًا فريدًا محفوظًا في جدول استقبال/Inbox مع unique constraint ومعالجة ذرية.

حتى يتم تنفيذ هذا الشرط في endpoint `/device/results`، يجب تصنيف اختبار إعادة الإرسال كـ**حاجز قبل الإنتاج**. لا يجوز استخدام last-write-wins أو دمج نتائج متعارضة تلقائيًا. إذا وصل نفس barcode بنتيجة مختلفة أو version مختلفة، يجب إنشاء conflict يدوي أو رفض العملية مع سجل تدقيق.

## 6. التحقق من التدقيق والمراقبة

بعد كل اختبار كتابة ناجح، يُراجع سجل التدقيق للتأكد من وجود المستخدم والمؤسسة ونوع المورد ومعرف الطلب وعدد النتائج. لا يجوز وضع القيمة السريرية الكاملة أو raw ASTM/HL7 أو access token في سجل device event أو monitoring metadata. ويجب مقارنة عدد الرسائل في outbox قبل وبعد الفشل، والتحقق من bounded retries وdead-letter وrecovery من stale processing.

في staging تُجمع correlation ID وrequest ID وdevice ID وconnector UID، مع حذف أسماء المرضى والمعرفات الوطنية من logs. يجب أيضًا اختبار أن مستخدمًا من المؤسسة الثانية لا يستطيع القراءة أو التعديل أو التأكيد على رسائل المؤسسة الأولى.

## 7. معايير قبول الإصدار

لا يُقبل التكامل للإنتاج إلا إذا نجحت اختبارات الخدمة والعقد وBackend والعزل المؤسسي، ونجح اختبار انقطاع الشبكة وإعادة الاتصال، وتمت مراجعة audit chain، ولم تظهر أسرار أو PHI في logs، ونجحت اختبارات Gitleaks وTrivy وSAST وdependency audit في CI. ويجب إجراء الاختبار النهائي ببيانات اصطناعية فقط مع خطة rollback ونسخة احتياطية معتمدة.

حاليًا، الاختبارات المحلية المثبتة هي **31 اختبارًا ناجحًا لخدمة device_bridge** و**20 اختبارًا ناجحًا لعقد Backend وdevice routes وoutbox**. هذه النتائج تثبت contract وtenant isolation الأساسيين، لكنها لا تثبت بعد idempotency عبر network retry أو التشغيل على staging حقيقي؛ لذلك تبقى تلك البنود حواجز مفتوحة قبل الإنتاج.

## المراجع الداخلية

[1]: ../services/device_bridge/app/integration/gula_client.py "GulaClient HTTP contract"
[2]: ../services/device_bridge/app/pipeline/data_pipeline.py "Device bridge pipeline"
[3]: ../backend/app/routes/device_results.py "Backend device result endpoint"
[4]: ../backend/app/devices/routes.py "Backend device-integration routes"
[5]: ../backend/tests/test_device_bridge_integration.py "Backend device bridge integration tests"
[6]: ../backend/tests/test_device_routes.py "Device integration route tests"
[7]: ../backend/tests/test_device_outbox.py "Device outbox tests"
