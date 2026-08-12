# GULA — تقرير اكتشاف خط الأساس

**الحالة:** `UPDATED — hardening implemented; production certification gates remain`

**تاريخ الفحص:** 11 أغسطس 2026

**الفرع:** `security-hardening-demo-alignment`

**HEAD:** `2de4932ef33aa104a1b8385a8d5df5391acf351b`

**المعد:** Manus AI

## 1. منهجية الفحص

تمت مراجعة مواصفة البرنامج الرئيسية وأمر التنفيذ الرئيسي المرفقين، ثم مقارنة قواعدهما بالمستودع الفعلي وبالدساتير والوثائق المعتمدة داخل المشروع. شملت المراجعة حالة Git، بنية الخلفية والواجهة والتطبيقات المحمولة/سطح المكتب، إعدادات قواعد البيانات والـRedis، حدود الـmiddleware، اختبارات الأمن والعزل والتزامن، وبوابات بناء الواجهة.

لا يُعد نجاح البناء وحده دليلاً على صلاحية منصة صحية حرجة. لذلك فُصلت النتائج إلى **مثبتة**، و**جزئية**، و**مخاطر مفتوحة**، و**غير متحققة في هذه البيئة**، مع إبقاء الملفات المعدّلة سابقاً خارج أي staging أو reset.

## 2. هوية المستودع وسلامته

| البند | الحالة | الدليل | المخاطر أو القيود |
|---|---|---|---|
| الفرع والـHEAD | مثبت | `git branch`, `git rev-parse HEAD` | الفرع متقدم محلياً عن الأصل بعملين سابقين، ويحتاج مراجعة دفع منفصلة |
| العمل غير الملتزم | موجود | `git status --short` أظهر 12 ملفاً معدلاً وملفات تدقيق وبيئة تشغيل غير متتبعة | لا يجوز استخدام `git add -A` أو `reset` أو تعديل عمل متزامن بلا فصل واضح |
| Worktrees | واحد | `git worktree list` أظهر worktree واحداً | لا يوجد worktree ثانٍ ظاهر، لكن وجود عملية Uvicorn يستلزم عدم قتلها بلا حاجة |
| الأسرار | غير مثبتة للإنتاج | إعدادات الإنتاج ترفض الأسرار الناقصة أو الضعيفة، بينما بيئة الديمو تستخدم مفاتيح مؤقتة | يجب إنشاء أسرار مستقرة ومدارة خارج المستودع قبل أي نشر إنتاجي |

## 3. المعمارية التنفيذية

تتكون المنصة من Backend مبني على FastAPI وSQLAlchemy/Alembic، وواجهة React/TypeScript/Vite حديثة في `frontend-v3`، ومسارات أقدم في `frontend` و`frontend-v2`، وتطبيقات mobile و`hospital_desktop`، إضافة إلى Docker وKubernetes وHelm وCloudflare وGitHub Actions. هذا يدعم مبدأ إعادة الاستخدام وعدم إعادة البناء، لكنه يزيد خطر اختلاف العقود بين المسارات القديمة والجديدة.

| المجال | الحالة | الدليل | التقييم |
|---|---|---|---|
| Backend API | `IMPLEMENTED` مع مخاطر متبقية | `backend/app`, `factory.py`, `main.py`, routes متعددة | واسع ومتكامل، ويحتاج اختباراً شاملاً بعد كل تغيير |
| Frontend v3 | `IMPLEMENTED` | `frontend-v3/src`, Vite/PWA | هو مسار البناء الحديث الظاهر، مع حاجة لقياس حجم الحزمة واختبارات E2E فعلية |
| Mobile/Desktop | `PARTIAL` | `mobile/`, `hospital_desktop/`, `docs/MOBILE_DESKTOP_STATUS.md` | وجود المصدر لا يثبت نجاح Android أو Windows EXE في هذه البيئة |
| Infrastructure | `IMPLEMENTED` جزئياً | Compose/Kubernetes/Helm/Nginx/Cloudflare | يحتاج تحقق نشر منفصل واستعادة وقياس load حقيقي |
| Interoperability | `PARTIAL` | FHIR/DHIS2/DICOM/تكاملات متعددة في الكود والتوثيق | بعض المسارات القديمة أو الاستعلامات تحتاج تحققاً على PostgreSQL |

## 4. الأمان والتفويض

يعلن المستودع Zero Trust وRBAC وABAC وعزل المستأجرين والتدقيق المتسلسل وتدوير الجلسات. بعد الإصلاحات، نجحت مجموعة Backend الكاملة في **2286 اختباراً**، كما نجحت اختبارات الأمن والتدقيق والعزل والتزامن وStartup Guard. تم نقل عقود الاختبار التي كانت تقرأ `main.py` إلى ملاكها التنفيذيين الفعليين في `factory.py` و`middleware.py` بدلاً من نسخ قائمة المسارات أو globals قديمة.

| الضابط | الحالة | الملاحظة |
|---|---|---|
| HttpOnly cookies وrefresh rotation | `IMPLEMENTED` حسب الكود والاختبارات السابقة | يجب اختبار Secure/SameSite وCORS في نشر HTTPS الفعلي |
| CSRF | `IMPLEMENTED` حسب التقرير والmiddleware | ينبغي إضافة اختبارات Origin/Referer وطلبات cookie لكل route group |
| RBAC/ABAC وعزل المستأجر | `CERTIFIED` جزئياً | اختبارات العزل الحرجة ناجحة؛ التغطية ليست شاملة لكل المجالات |
| rate limiting وdegradation | `IMPLEMENTED` جزئياً | fallback الداخلي مسموح فقط في demo/dev/test؛ production يبقى fail-closed ويتطلب Redis مشتركاً للتوسع |
| security headers | `CERTIFIED` على مستوى regression | أضيف `Cross-Origin-Resource-Policy: same-site` ومنع `payment=()` مع اختبارات response headers؛ يلزم smoke على HTTPS الفعلي |
| secrets | `IMPLEMENTED` للرفض في الإنتاج | الإعداد المحلي يحذر ويولد مفاتيح مؤقتة؛ هذا مقبول للديمو فقط لا للإنتاج |
| audit immutability | `CERTIFIED` cross-dialect على مستوى hash | تم تطبيع timestamp إلى UTC ISO microseconds داخل chain hash، مع اختبار naive/aware؛ يلزم PostgreSQL restore/verification قبل اعتماد الإنتاج |

## 5. البيانات وقاعدة البيانات

PostgreSQL هو المحرك الأساسي، وRedis طبقة cache/pub-sub وليست مخزناً أساسياً. إعداد pool الحالي قابل للضبط ويستخدم `pool_pre_ping` وstatement timeout وidle transaction timeout على PostgreSQL، بينما يستخدم SQLite `StaticPool` للديمو والاختبارات. هذا يتيح التشغيل المحلي لكنه لا يمثل حمولة الإنتاج؛ يجب عدم استخلاص أرقام أداء وطنية من SQLite أو TestClient داخل العملية.

أعيد فحص سلسلة Alembic: لا توجد revision IDs مكررة، ونجح بناء SQLite جديد من الصفر حتى `20260723_0002 (head)`. لم يُنفذ round-trip على PostgreSQL في هذه البيئة، لذلك تبقى مصادقة PostgreSQL وrestore drill بوابتين منفصلتين قبل اعتماد الإنتاج.

## 6. الأداء والاعتمادية

بوابات Frontend v3 نجحت في `lint` و`typecheck` و`test` و`build`؛ لا توجد unit tests فعلية حالياً، لكن Vitest ينجح صراحةً مع `--passWithNoTests`. استغرق بناء Vite الأخير نحو 503ms في إعادة التحقق، وكانت الحزمة الرئيسية المضغوطة نحو 131KB.

أضيف launcher محلي يدعم `WEB_CONCURRENCY` مع default يساوي عاملاً واحداً عند SQLite Demo وعاملين عند PostgreSQL، ضمن صيغة pool الموثقة. كما أصبح `/health` liveness خفيفاً لا يفتح اتصال DB، بينما بقي `/health/ready` و`/health/status` للتحقق التشخيصي. في القياس النهائي read-only على خدمة Demo المحلية وSQLite، نجحت 120/120 طلباً عند concurrency=20 بلا 503 وبنحو 59.9 RPS، مع p50≈233ms وp95≈918ms. وعند concurrency=1 قبل هذا التحسين كان p95≈8ms؛ هذه النتيجة تثبت عدم الانهيار المحلي وتحسن healthcheck load، لكنها لا تثبت هدف peak p95=500ms على PostgreSQL/Redis الإنتاجيين.

## 7. بوابات الجودة المنفذة

| البوابة | النتيجة الحالية | الدليل |
|---|---|---|
| Python compileall | ناجحة | `python3.12 -m compileall -q backend/app backend/tests` |
| Frontend typecheck | ناجحة | `cd frontend-v3 && npm run typecheck` |
| Frontend lint | ناجحة | `cd frontend-v3 && npm run lint` |
| Frontend tests | ناجحة | `cd frontend-v3 && npm run test` |
| Frontend production build | ناجحة | `cd frontend-v3 && npm run build` |
| Backend full suite | 2286 ناجحاً، 251 تحذيراً غير حاجز | `/usr/local/bin/pytest -q` بعد آخر تحسين liveness، مدة نحو 4:18 |
| Backend compileall | ناجح | `python3.12 -m compileall -q backend/app backend/tests` |
| Fresh SQLite migration | ناجحة حتى head | قاعدة `/tmp/gula_fresh_migration_final.db` وصلت إلى `20260723_0002 (head)` |
| Frontend lint/typecheck/test/build | 0/0/0/0 | بوابات `frontend-v3` نجحت؛ لا توجد unit tests فعلية |
| Native Android/Windows build | غير متحقق | الأدوات الأصلية ليست متاحة في هذه البيئة |
| Production PostgreSQL load | غير متحقق | القياس الحالي read-only على demo/SQLite فقط |

## 8. المخاطر الفورية التي لا يجوز تجاهلها

أُغلقت المخاطر المثبتة في هذه الجولة: فحص duplicate revisions نظيف، استعلام DHIS2 أصبح tenant-scoped عبر `lab_orders`, تطبيع audit hash أصبح cross-dialect، وDemo seed صار متوافقاً مع النماذج الحالية وقابلاً للتكرار. ما يزال `LabResult.version` غير مفعّل في mutation path مستقل لأن المسارات الحالية لا تعرض تحريراً بعد الإنشاء؛ يجب فتح Change Control قبل إضافة تحرير سريري. كما تبقى PostgreSQL load، Redis HA، backup/restore، وnative builds بوابات نشر غير متحققة.

## 9. قرارات النطاق

نُفذ نطاق الجولة دون تغيير workflow السريري: إصلاح DHIS2 tenant scope، تقوية headers، ضبط Startup Guard بحيث يكون fallback Redis سريعاً ومحصوراً في البيئات غير الإنتاجية، توحيد audit timestamp، تقصير مدد JWT الافتراضية إلى 15 دقيقة و7 أيام، إصلاح Demo bootstrap وlegacy subscription seed، دعم workers في launcher، وإضافة قياس read-only واختبارات regression. تبقى offline sync، تحرير النتائج مع CAS، PostgreSQL load، وbackup/restore موجات مستقلة تتطلب اعتماداً.

## المراجع

[1]: ../upload/GULA_MASTER_PROGRAM_SPECIFICATION.md "GULA Master Program Specification"
[2]: ../upload/GULA_MASTER_AI_AGENT_EXECUTION_COMMAND_v1.0.md "GULA Master AI Agent Execution Command"
[3]: docs/PRODUCTION_HARDENING.md "Production Hardening Report"
[4]: docs/security/security_baseline.md "Security Baseline"
[5]: docs/constitution/08_SECURITY_CONSTITUTION.md "Security Constitution"
[6]: docs/constitution/14_API_CONSTITUTION.md "API Constitution"
[7]: docs/constitution/15_DATABASE_CONSTITUTION.md "Database Constitution"
[8]: docs/constitution/runtime/06_performance_certification.md "Performance Certification"
