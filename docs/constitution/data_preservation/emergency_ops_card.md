# بطاقة عمليات الطوارئ (Emergency Operations Card)
**منصة غولا (GULA) - استجابة سريعة**

في حال حدوث عطل في المنصة، اتبع هذا الدليل المختصر للاستعادة الفورية.

## 1. التشخيص السريع (Rapid Triage)
تحقق من حالة المكونات الأساسية:
```bash
# فحص حالة الحاويات
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# فحص جاهزية الخلفية (Backend)
curl -f http://localhost:8000/health/ready

# فحص سجلات الأخطاء الأخيرة
docker logs --tail 50 gula-backend | grep ERROR
```

## 2. سيناريوهات الاستعادة (Recovery Scenarios)

### أ. تعطل قاعدة البيانات (PostgreSQL Down)
إذا كانت الخلفية تعطي خطأ `DB Connection Refused`:
1. تأكد من عمل حاوية قاعدة البيانات: `docker start gula-postgres`
2. تحقق من السجلات: `docker logs gula-postgres`
3. إذا فشل البدء بسبب تلف الملفات، استخدم آخر نسخة احتياطية:
   `bash scripts/dr_recovery.sh verify` (للتحقق) ثم اتبع خطوات الاستعادة.

### ب. تعطل الخدمة (Backend Crash)
إذا كانت الحاوية تعمل ولكن الاستجابة بطيئة أو تعطي 500:
1. أعد تشغيل الخدمة: `docker restart gula-backend`
2. تحقق من استهلاك الذاكرة: `docker stats gula-backend`
3. إذا استمر العطل، تحقق من سلامة الكود: `bash scripts/preflight.sh`

### ج. اختناق الموارد (Resource Exhaustion)
إذا كان المعالج (CPU) أو الذاكرة 100%:
1. حدد الحاوية المستهلكة: `docker stats`
2. قم بزيادة عدد العمال مؤقتاً أو أعد التشغيل لتفريغ الذاكرة.
3. شغل سكريبت الصيانة لتخفيف العبء عن قاعدة البيانات:
   `bash scripts/db_maintenance.sh`

## 3. التحقق النهائي بعد الإصلاح
بعد كل عملية إصلاح، **يجب** تشغيل:
```bash
# التحقق من سلامة البيانات وسجل التدقيق
python3 scripts/audit_verifier.py
```

## 4. جهات الاتصال للطوارئ
- **المسؤول التقني:** [أدخل الاسم/الرقم]
- **دعم الاستضافة:** DigitalOcean Support
- **قناة البلاغات:** Slack #incidents
