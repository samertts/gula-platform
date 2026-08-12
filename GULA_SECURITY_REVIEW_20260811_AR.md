# تقرير المراجعة الأمنية والتشغيلية — GULA Platform

**التاريخ:** 11 أغسطس 2026

**النطاق:** المستودع الكامل، مع تركيز إضافي على الملفات المعدلة ومسارات المصادقة، الجلسات، قاعدة البيانات، المهاجرات، التشغيل الذاتي، والواجهة الحديثة `frontend-v3`.

## الخلاصة التنفيذية

أُجريت مراجعة ثابتة واعتمادية بعد تنفيذ تغييرات التقوية السابقة، ثم أُصلحت ثغرتان مثبتتان في نطاق الجولة. الأولى كانت تركيب JSON داخل استعلام SQL في `backend/app/ai/knowledge_graph.py`؛ إذ كان محتوى `aliases` و`properties` يندمج داخل النص SQL قبل التنفيذ. استُبدل ذلك باستخدام نموذج SQLAlchemy وربط القيم كمعاملات JSONB، وأضيف اختبار regression يحتوي على اقتباس ومحاولة SQL وهمية ويتحقق من حفظها كبيانات فقط. الثانية كانت تعطيل التحقق من شهادات TLS في `scripts/self_heal.py` عبر `verify=False`. أصبح التحقق مفعلاً افتراضياً، ولا يمكن تعطيله إلا بإعداد تشغيلي صريح `ASHS_VERIFY_TLS=false`، مع رفض القيم غير المعروفة.

> **نتيجة التدقيق:** لا توجد ثغرة اعتماديات معروفة حسب `pip-audit` و`npm audit`، ولا توجد مفاتيح خاصة أو رموز وصول حقيقية في الملفات المصدرية التي فُحصت. لا يعني ذلك أن المنصة أصبحت معتمدة إنتاجياً؛ ما زالت اختبارات PostgreSQL/Redis الإنتاجية، الاستعادة، والبناء الأصلي للتطبيقات بوابات مستقلة.

## نتائج الفحوص

| الفحص | النتيجة | الدليل |
|---|---:|---|
| Backend full suite | **2287 ناجحاً**، 251 تحذيراً غير حاجز | `/usr/local/bin/pytest -q` |
| اختبارات الإصلاحات الأمنية المركزة | **97 ناجحاً** | KnowledgeGraph وSecurity وPerformance وStartup Guard |
| Frontend lint | ناجح | `npm run lint` |
| Frontend typecheck | ناجح | `npm run typecheck` |
| Frontend test | ناجح بلا ملفات unit فعلية | Vitest مع `--passWithNoTests` |
| Frontend build | ناجح | Vite/PWA production build |
| Python dependencies | صفر ثغرات معروفة | `pip-audit -r backend/requirements.txt` |
| Node production dependencies | صفر ثغرات | `npm audit --omit=dev --audit-level=moderate` |
| Python compileall | ناجح | `python3.12 -m compileall -q backend/app backend/tests scripts/self_heal.py` |
| Git whitespace gate | ناجح | `git diff --check` |
| Source secret scan | لا مفاتيح أو tokens حقيقية مكتشفة | فحص markers للمفاتيح والرموز مع استثناء fixtures والتوثيق |

## الإصلاحات الأمنية المنفذة

| المعرّف | الموقع | المشكلة | الإصلاح |
|---|---|---|---|
| SEC-SQL-01 | `backend/app/ai/knowledge_graph.py` | إدراج JSON داخل SQL عبر f-string، بما يسمح بكسر literal عند احتواء القيمة على اقتباس | استخدام `AIKnowledgeNode` وSQLAlchemy ORM binding للقيم، مع اختبار JSON hostile input |
| SEC-TLS-01 | `scripts/self_heal.py` | `requests.get(..., verify=False)` يعطل التحقق من شهادة TLS | `TLS_VERIFY=true` افتراضياً، وإتاحة false فقط عبر إعداد صريح موثق ومتحقق |
| SEC-AUTH-01 | `frontend-v3/src/api/client.ts` | خطر عودة تخزين JWT في المتصفح | التحقق من بقاء `withCredentials` والكوكيز HttpOnly؛ لم يظهر تخزين access/refresh token في localStorage ضمن كود التطبيق |
| SEC-HEADERS-01 | `backend/app/middleware.py` | نقص CORP وسياسة payment | إضافة `Cross-Origin-Resource-Policy: same-site` و`Permissions-Policy` التي تقفل `payment=()` مع regression tests |
| SEC-STARTUP-01 | `backend/app/core/startup_guard.py` | fallback Redis قد يسبب boot loop أو fail-open غير مضبوط | السماح المحدود في demo/dev/test ورفضه في production، مع اختبارات السياسة |

## إشارات فحص صُنفت كغير ثغرات

ظهرت عبارات `BEGIN ... PRIVATE KEY` داخل كاشف الأسرار نفسه ووثائق أسماء متغيرات النشر، لا كمفاتيح فعلية. كما ظهرت كلمات مرور داخل fixtures واختبارات محلية، ولا تستخدم كأسرار نشر. استخدام `localStorage` في الواجهة الحديثة محصور في اللغة والمظهر، بينما ظهور token في اختبار E2E يخص حذف بيانات اختبار قديمة ولا يمثل مسار المصادقة التشغيلي. أما SQL الديناميكي المتبقي في vector store وreference repository والمهاجرات فيستخدم عبارات أو أسماء داخلية ثابتة، والقيم الخارجية مربوطة كمعاملات؛ ويجب إبقاء هذا القيد ضمن مراجعة أي تغيير لاحق.

## المخاطر المتبقية وقرار النشر

لا يجوز اعتبار هذه المراجعة تصريح جاهزية إنتاجية. ما زالت هناك تحذيرات deprecation وSQLAlchemy teardown في الاختبارات، ولا توجد unit tests فعلية للواجهة، كما لم تُنفذ في هذه البيئة عمليات build أصلية لـAndroid أوWindows EXE. كذلك لم تُثبت أهداف p95 على PostgreSQL وRedis منفصلين، ولم تُنفذ تجربة backup/restore أو outage drill متعدد العمال. يجب إغلاق هذه البنود عبر CI وبيئة staging مماثلة للإنتاج قبل فتح المنصة الصحية للعامة.

يجب أن تتم أي عملية نشر لاحقة باستخدام أسرار مستقرة ومدارة خارج المستودع، وRedis مشترك في الإنتاج، وTLS موثق، وقاعدة PostgreSQL منفصلة لوضع Demo. لا يجوز استخدام قاعدة Demo أو مفاتيح البيئة المحلية كبديل عن عزل الإنتاج.

## الملفات التي تستحق المراجعة في كل Pull Request

يجب إعطاء عناية خاصة لأي تغيير في `backend/app/middleware.py`, `backend/app/core/startup_guard.py`, `backend/app/database.py`, `backend/app/routes/`, `backend/app/services/audit_service.py`, `backend/app/models/`, `backend/migrations/versions/`, `frontend-v3/src/api/`, و`scripts/`. ويجب أن يمر كل تغيير على فحوص الأسرار والاعتماديات، اختبارات العزل والتدقيق، compileall، وبوابات الواجهة قبل الدمج.
