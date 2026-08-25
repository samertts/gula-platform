# دليل احتواء gateway الأجهزة التجريبي

**الفرع:** `fix/legacy-device-gateway-containment`
**القاعدة:** `release/clinical-safety-2026q3-rc1` عند `dfd93962`
**التزام التنفيذ:** `c36895ac`

## الخطر المحتوى

كان `backend/gateway/device_gateway.py` مساراً تجريبياً مستقلاً يفتح raw TCP socket ويرسل قيماً محللة مباشرة عبر HTTP مع عنوان وtoken افتراضيين. لا يظهر مسار تشغيل موثق أو deployment reference له داخل RC1، لكنه يناقض احتواء الأجهزة وdefault-deny ولا يصلح كطريق سريري أو كبديل لـDevice Bridge.

## التغيير

استبدل الملف بحاجز fail-closed. لا يستورد socket أو HTTP client، ولا يملك عنواناً أو token افتراضياً، وترفض الدوال السابقة `parse_message` و`send_result` و`run_server` جميعها بـ`LegacyDeviceGatewayDisabledError` مع سجل عملية مجرد. لا تنشئ هذه الدوال نتيجة أو طلب شبكة أو socket.

## الأدلة

| الفحص | النتيجة |
|---|---|
| اختبار الاحتواء الجديد | PASS: يثبت الرفض وغياب socket/HTTP/token الافتراضي من المصدر. |
| Ruff وMyPy للملفين | PASS. |
| backend regression من `backend/` | 2743 passed, 4 skipped, 249 warnings. |
| changed-files gate مقابل RC1 | PASS؛ Ruff `0→0` وMyPy `5→0` للملفات المتغيرة. |

## الحدود والمتطلبات التالية

لا يحول الاحتواء gateway القديم إلى integration حي. أي بديل يجب أن يمر عبر تصميم Device Bridge: forwarding معطل افتراضياً، HTTPS/mTLS وشهادات خارج Git، gateway مع allow-list/replay controls، عزل tenant، حارس أوامر سريرية، ومراجعة شبكة وUAT تركيبية وتوقيعات مخولين. لم تنشأ شهادات أو secrets أو device connection في هذه الدفعة، ولذلك يظل GO NO-GO.
