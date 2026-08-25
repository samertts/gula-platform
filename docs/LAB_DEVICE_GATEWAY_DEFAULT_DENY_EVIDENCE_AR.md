# دليل default-deny لمسار Lab Device Gateway القديم

**الفرع:** `fix/lab-device-gateway-default-deny`
**القاعدة:** `release/clinical-safety-2026q3-rc1` عند `dfd93962`
**التزام التنفيذ:** `8db852be`

## سبب الحظر

كان gateway القديم يمر من تحقق HMAC/allowlist/nonce ثم يعيد envelope بحالة `received` حتى مع عدم وجود مستهلك application أو deployment reference لمسار `receive_device_result`. هذا ليس Device Bridge معتمداً، وليس مسار InstrumentMeasurement quarantine، وقد يسمح باستنتاج خاطئ بأن قبول إدخال جهاز قد تم.

## التغيير

أزيل منطق parsing وHMAC وnonce/replay النشط من gateway القديم واستبدل بواجهة default-deny. كل استدعاء لـ`receive_device_result` يسجل سبباً مجرداً ويرفع `DeviceAuthError` قبل parsing أو قبول أو كتابة. لا يحتوي الملف على HMAC أو cache replay أو `LabResult` أو commit أو اتصال شبكة.

## التحقق

| الفحص | النتيجة |
|---|---|
| جرد المستهلكين | لا caller تشغيلي أو route import أو deployment reference لـ`receive_device_result`؛ النتائج الوحيدة artifacts/تقارير أو الاختبار. |
| اختبارات gateway | 2 passed: envelope اصطناعي مع حقول توقيع/nonce يرفض، ولا يوجد مسار قبول نشط. |
| Ruff وMyPy | PASS. |
| backend regression من `backend/` | 2740 passed, 4 skipped, 249 warnings. |
| changed-files gate مقابل RC1 | PASS؛ Ruff `0→0` وMyPy `2→0`. |

## الحدود

الحظر لا ينفذ جهازاً حياً ولا ينشئ مساراً بديلاً. المسار الوحيد المرشح مستقبلاً يجب أن يلتزم بـDevice Bridge fail-closed، mTLS وPKI خارج Git، network review، tenant isolation، quarantine، مراجعة بشرية، وUAT تركيبية. لا يغير هذا الدليل حالة GO؛ تبقى NO-GO حتى الأدلة الخارجية والتوقيعات المخولة.
