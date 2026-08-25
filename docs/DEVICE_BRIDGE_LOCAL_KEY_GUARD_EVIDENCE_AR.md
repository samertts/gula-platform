# دليل حارس مفتاح التشغيل المحلي لـDevice Bridge

**الفرع:** `docs/device-bridge-operational-safety`
**القاعدة:** `fix/device-bridge-mtls-fail-closed` عند `6cf17508`
**التزام التنفيذ:** `f89c1502`

## المشكلة المصححة

كان `services/device_bridge/Makefile` يضع قيمة ثابتة لمتغير `API_KEY`، كما يعرض README نفس القيمة. هذه قيمة تطوير معروفة وليست secret مناسباً للتشغيل، وقد تشجع تشغيل API محلياً من دون إدخال قيمة صريحة.

## المعالجة

أزيلت القيمة الافتراضية وأضيف target `require-api-key`. يفشل `make run` و`make smoke` برمز خروج 2 إذا غاب `API_KEY`. يوضح README توليد قيمة محلية عشوائية مؤقتة، ويحظر الالتزام بها أو استعمال credential إنتاجي. كما يوضح أن forwarding العلوي معطل في runtime المنشور، وأن emulator وsmoke check يستخدمان بيانات تركيبية فقط.

## التحقق

| الفحص | النتيجة |
|---|---|
| `make require-api-key` بلا `API_KEY` | رفض مقصود برمز 2. |
| `API_KEY=synthetic-local-key make -n run` | أمر تشغيل صالح مع قيمة صريحة فقط. |
| Device Bridge suite | 34 passed, 1 warning. |
| Ruff للاختبار الجديد | PASS. |
| MyPy للاختبار الجديد | PASS. |
| بوابة changed-files مقابل C6 | PASS؛ Ruff `0→0` وMyPy `0→0` للملف المتغير. |

## الحدود

لا يخلق هذا الفرع شهادة أو مفتاحاً إنتاجياً ولا يرسل secrets إلى Git أو CI. ولا يفعّل forwarding أو HTTP أو جهازاً حياً. يبقى النشر الحي مرهوناً بـPKI وsecret manager وgateway mTLS ومراجعة شبكة وUAT تركيبية وتوقيعات الملاك، ولذلك تظل الحالة NO-GO.
