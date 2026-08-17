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

## 6. إغلاق التحذيرات غير الوطنية

تمت مراجعة تحذيرات `audit_coverage` الثلاثين التي شملت مسارات الذكاء الاصطناعي، الصلاحيات، المرضى المرجعيين، مسار الرعاية المستمرة، السجل الإلكتروني، المستشفى، البيانات الوطنية، البث، OAuth2، الحسابات الخدمية، الحوكمة، والمراجع. الكتابات المباشرة والمسارات المفوضة إلى الخدمات أصبحت مغطاة بواسطة `audit_route_mutation`، بينما بقيت helpers التي تستدعي `log_action` مباشرة مدعومة في تحليل Security Gate بدل إنشاء سجل مكرر.

يسجل decorator المركزي نجاح العملية بعد تنفيذ route، ويستخدم `audit_mutation` الذي يضيف المستخدم والدور و`lab_id` واسم المسار ونوع المورد إلى السجل hash-chained. لا تُحفظ استجابة سريرية أو أسرار OAuth داخل payload؛ ويُسجل أن before/after العام محجوبان عندما لا يتوفر snapshot دلالي آمن في طبقة route. المسارات التي تحتاج before/after سريريًا مفصلًا يجب أن تضيفه داخل service transaction قبل rollout السريري.

| النتيجة | القيمة |
|---|---:|
| تحذيرات `audit_coverage` قبل الإصلاح | 30 |
| تحذيرات `audit_coverage` بعد الإصلاح | 0 |
| اختبارات التغطية الأمنية الجديدة | 2 |
| المجموعة الأمنية المركزة | 45 اختبارًا ناجحًا |
| Backend suite الرسمية | 2686 اختبارًا ناجحًا، 4 متجاوزة، 252 تحذيرًا |

أضيف اختبار regression يثبت أن decorator ينشئ سجلًا قابلًا للاستعلام، ويمنع تسريب حقل سري من response، ويتحقق آليًا من أن Security Gate لا يعيد أي finding في تغطية التدقيق. أما الاختبارات الاثنا عشر القديمة تحت `services/device_bridge/tests` فتظل خارج Backend suite بسبب أخطاء import وتجميع تاريخية غير مرتبطة بهذه الدفعة، ويجب فصلها أو إصلاحها في مهمة مستقلة.

> صفر تحذيرات في AST لا يساوي موافقة إنتاج. يجب استكمال تشغيل SAST وGitleaks وdependency/container/IaC scans على CI نظيف، ثم اختبار تكامل staging ومراجعة اختراق مستقلة.

## 7. التحقق الخاص بهذه الدفعة

```bash
PYTHONPATH=backend pytest -q \
  backend/tests/test_non_national_audit_coverage.py \
  backend/tests/test_platform_security_hardening.py \
  backend/tests/test_security_regression.py \
  backend/tests/test_sync_security_and_outbox.py

PYTHONPATH=backend pytest -q backend/tests

python3 config/quality-gates/security-gate.py \
  --skip-sast --skip-deps --skip-secrets --skip-container \
  --skip-iac --skip-sbom --skip-credentials --json
```

يجب تنفيذ الأمر الأخير دون خيارات `skip` في CI الإنتاجي بعد تثبيت الأدوات الخارجية؛ خيارات التجاوز استُخدمت محليًا فقط لأن الأدوات غير مثبتة في البيئة الحالية.

## 8. نتائج فحوص CI الأمنية اللاحقة

بعد موافقة استكمال الفحوص، تم تثبيت أدوات Bandit وSemgrep وSafety وCheckov وpip-audit محليًا وتشغيل Security Gate الكامل على commit العمل. أظهرت الجولة الأولى **37 خطأ و2 تحذير**؛ وبعد التحليل والإصلاح انخفضت النتيجة إلى **0 أخطاء و7 تحذيرات بيئية أو اختبارية**.

شملت الإصلاحات استبدال concatenation في استعلامات demo data بـbound parameters، وتوثيق SQL الداخلي الآمن في migration وoffline store وSNDHS backfill بتعليقات suppression مرتبطة ب allowlist وbind parameters، وإضافة `HEALTHCHECK` إلى صور Python، وتحويل frontend runtime إلى `nginx-unprivileged` على المنفذ 8080 مع `USER nginx`. كما تم إصلاح parsing لنتيجة Bandit عند ظهور progress output، وتحسين credential scanner حتى لا يحول labels النصية وملفات scanner نفسها إلى secrets، ويصنف fixtures الاختبارية كتحذيرات غير إنتاجية.

تمت إزالة القيم السرية الفعلية من `security-audit/secret-report.md` واستبدالها بـ`<REDACTED>`. إذا كانت هذه القيم قد استُخدمت خارج بيئة اختبار معزولة، يجب تدويرها فورًا من مصدر الأسرار؛ redaction من Git لا يلغي وجودها في التاريخ السابق.

| الفحص | النتيجة النهائية المحلية |
|---|---:|
| Bandit HIGH/CRITICAL | 0 |
| Semgrep HIGH/CRITICAL | 0 |
| Safety dependencies | 0 vulnerabilities |
| Checkov Docker/IaC | 0 violations |
| SBOM blocked licenses | 0 |
| Audit coverage | 0 findings |
| Gitleaks | لم يُنفذ: binary غير مثبت |
| Trivy | لم يُنفذ: binary غير مثبت |
| Credential fixtures | 5 تحذيرات اختبارية فقط |

نجحت Backend suite بعد هذه الدفعة في **2686 اختبارًا، مع 4 متجاوزة و252 تحذيرًا**، ونجحت مجموعة الاختبارات الأمنية المتأثرة في **54 اختبارًا**. بوابة الجاهزية الحكومية نجحت في **67 اختبارًا، مع 4 تحذيرات**؛ التحذير الوحيد التشغيلي هو أن فحص production environment لم يُطلب باستخدام `--production`. لا يوجد عنوان staging أو token متاح في الجلسة الحالية، لذلك لم يُنفذ اختبار load أو smoke خارجي على مؤسسة صحية حقيقية.

> لا تعتبر نتيجة Security Gate المحلية موافقة إنتاج؛ يجب تشغيل Gitleaks وTrivy داخل CI أو runner مجهز، ثم تنفيذ staging smoke وload ببيانات اصطناعية فقط، مع تدوير أي سر تاريخي مكشوف.
