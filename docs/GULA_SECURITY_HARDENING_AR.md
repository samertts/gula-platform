# تقوية الحماية الأمنية لمنصة GULA

**التاريخ:** 2026-08-17
**النطاق:** المصادقة، الجلسات، عزل المؤسسات، CSRF، CORS، Security Headers، Patient Flow وOffline Sync
**الفرع:** `manus/government-patient-flow`

> هذه الوثيقة توثق إصلاحات أمنية قابلة للمراجعة، ولا تمنح موافقة إنتاج حكومية تلقائية. يلزم تشغيل أدوات الفحص الخارجية، واختبار staging، ومراجعة أمنية مستقلة قبل أي rollout سريري.

## 1. الإصلاحات المنفذة

| المجال | الضابط المنفذ | أثر الحماية |
|---|---|---|
| JWT access/refresh | رفض token بلا `jti`، مع استمرار فرض `exp` و`iat` ونوع token الصحيح. | يمنع إصدار token لا يمكن إبطاله أو تتبعه عبر blacklist. |
| Scope consistency | مطابقة `user_id` و`lab_id` و`role` داخل JWT مع السجل الخادمي، ورفض `perm_ver` غير الصحيح. | يمنع إعادة استخدام token قديم بعد نقل المستخدم بين المؤسسات أو تغيير دوره. |
| CSRF | فحص Origin/Referer للطلبات المتغيرة عند وجود `access_token` أو `refresh_token` cookie، مع fail-closed للمتصفحات التي لا ترسل أيهما. | يمنع form-based CSRF على مسارات الجلسات والتحديث والخروج. |
| CORS | إضافة `X-Device-Session` إلى allowlist مع إبقاء origins صريحة ومنع `*` وفرض HTTPS في production/staging. | يسمح بالمزامنة المشفرة دون توسيع نطاق origins. |
| Security Headers | تطبيق headers على API والملفات الثابتة، بما في ذلك CSP وHSTS في البيئات الآمنة و`X-Permitted-Cross-Domain-Policies: none`. | يقلل مخاطر MIME sniffing وclickjacking وتسريب referrer وتحميل الموارد غير المصرح. |
| Offline Sync | rate limit لتسجيل جلسة الجهاز والدفعات، مع RBAC ورمز جلسة الجهاز وعزل المؤسسة الموجودين مسبقًا. | يقلل إساءة استخدام endpoint وإعادة الإرسال المكثف. |
| التدقيق | إبقاء كل عمليات المزامنة ومسارات Patient Flow ضمن audit chain، مع before/after في المسارات الوطنية المعدلة. | يحافظ على قابلية التحقيق وعدم إنكار العملية. |

## 2. نتائج الاختبار

نجحت مجموعة الاختبارات الأمنية المركزة في **43 اختبارًا**، وشملت JWT وperm_version وعزل المؤسسة وCSRF وCORS وSecurity Headers وRBAC وOffline Sync وPatient Flow. كما نجح `compileall` للملفات المعدلة.

بعد إضافة صلاحيات router-level لمسارات National السريرية وإغلاق IDOR في سجل التدقيق، نجحت مجموعة Backend الكاملة في **2684 اختبارًا، مع 4 اختبارات متجاوزة و252 تحذيرًا غير حاجب**. تم توسيع `government_readiness_gate.py` ليشغل اختبارات Security Regression وPlatform Security وSync وPatient Flow وStress ضمن فحص الجاهزية.

يجب تشغيل مجموعة Backend الكاملة بعد كل commit أمني، إضافة إلى Security Gate الكامل. لا تعتبر أدوات SAST وdependency scan وsecret scan منفذة محليًا إذا لم تكن الأدوات نفسها مثبتة؛ يجب أن يكون تنفيذها في CI أو staging واضحًا في سجل الإصدار.

## 3. متطلبات ما قبل الإنتاج

قبل الإنتاج الحكومي يجب تشغيل Bandit أو Semgrep، وGitleaks، وdependency scanner، وفحص الحاوية وIaC على نسخة نظيفة من الفرع. كما يجب اختبار preflight CORS من النطاق الفعلي، ورفض Origin غير مصرح، وCSRF بالـrefresh cookie، وتدوير refresh token بعد الاستخدام، وإبطال الجلسات بعد تغيير الدور أو المؤسسة.

يجب تشغيل اختبار اختراق مستقل يغطي IDOR وcross-tenant access وJWT confusion وsession fixation وrefresh replay وdevice-session theft وrate-limit bypass وCSP bypass. يجب استخدام بيانات اصطناعية فقط في staging، وعدم اعتبار نجاح الاختبارات الوحدية دليلًا على سلامة تكامل TLS أو WAF أو broker أو HSM.

## 4. الحدود والمخاطر المتبقية

لا تزال هناك حاجة إلى إدارة مفاتيح مؤسسية مثل HSM أو KMS، وربط جلسات الأجهزة بـMDM، وتشغيل broker فعلي لـOutbox، وتفعيل مراقبة blacklist وrate-limit على Redis مشترك بين جميع عقد API. كما يجب إغلاق تحذيرات Security Gate غير الوطنية المتبقية route-by-route، وعدم تحويلها إلى استثناءات صامتة.

يجب عدم تطبيق أي migration على قاعدة حكومية إنتاجية قبل مراجعة SQL ونسخة احتياطية قابلة للاستعادة واختبار rollback واعتماد تغيير رسمي.

## 5. أوامر التحقق

```bash
PYTHONPATH=backend pytest -q \
  backend/tests/test_platform_security_hardening.py \
  backend/tests/test_security_regression.py \
  backend/tests/test_sync_security_and_outbox.py

python3 -m compileall -q backend/app
python3 config/quality-gates/security-gate.py --json
```

في حال غياب أدوات الفحص الخارجية، يجب تسجيل ذلك كفشل في بوابة الإصدار أو كعنصر مفتوح، وليس كنجاح أمني.
