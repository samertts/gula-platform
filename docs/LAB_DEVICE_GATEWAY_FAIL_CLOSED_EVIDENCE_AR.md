# دليل Lab Device Gateway: fail-closed وتحسين الأنواع

**الفرع:** `fix/lab-device-gateway-types`
**القاعدة:** `release/clinical-safety-2026q3-rc1` عند `dfd93962`
**التزام التنفيذ:** `40dfa8da`

## نتيجة المراجعة

المسار `backend/app/gateways/lab_device_gateway.py` لا ينشئ `LabResult` ولا يستورد جلسة قاعدة بيانات ولا ينفذ commit. وظيفته الحالية تقبل envelope في الذاكرة فقط بعد HMAC وallowlist وtimestamp وnonce replay check. يفشل مغلقاً عند غياب مفتاح HMAC أو allowlist أو nonce أو replay store.

## التحسين

أضيفت أنواع صريحة لمدخل البيانات غير الموثوقة ولمخرج envelope. يبقى `value` من نوع `Any` عمداً لأن الدالة هي حد تحقق وقت تشغيل يقبل input غير موثوق ثم يحوله أو يرفضه. لم يتغير HMAC أو replay window أو عزل الجهاز أو حالة الإرجاع.

## التحقق

| الفحص | النتيجة |
|---|---|
| اختبارات `test_lab_device_gateway_fail_closed.py` | 4 passed: غياب HMAC، غياب allowlist، تعطل replay store، ورفض replay. |
| فحص مراجع persistence | لا `LabResult` أو `Session` أو `commit` أو `database` في gateway. |
| Ruff | PASS. |
| MyPy للـgateway والاختبار | PASS؛ انخفضت أخطاء الملفات المتغيرة من 2 إلى 0. |
| changed-files gate مقابل RC1 | PASS؛ Ruff `0→0` وMyPy `2→0`. |

## حدود السلامة

قبول envelope ليس قبول نتيجة سريرية ولا يفتح مساراً حياً. لا يستطيع هذا gateway تجاوز sample verification أو InstrumentMeasurement quarantine أو ClinicalCommandGuard أو حوكمة مراجعة بشرية. يبقى توصيل جهاز حقيقي أو PKI/mTLS أو UAT أو إصدار نتيجة محظوراً خارج هذه الدفعة، ولذلك تظل حالة GO NO-GO.
