# GULA — Current Repository State

**تاريخ الاستعادة:** 11 أغسطس 2026

**المستودع:** [samertts/gula-platform](https://github.com/samertts/gula-platform)

**الفرع الحالي:** `wave0-audit-hardening-20260811`

**HEAD المحلي/المدفوع:** `2fb4fd11` (`security: complete wave 0 audit and hardening`)

## الحالة التنفيذية

المستودع ليس فارغاً، ويحتوي على Backend واسع مبني على FastAPI وSQLAlchemy/Alembic، واجهة React/Vite حديثة في `frontend-v3`، مسارات واجهة أقدم، Android/Kotlin، Flutter Desktop، ومجموعة كبيرة من خدمات التكامل والبنية التحتية. أُنشئ فرع `wave0-audit-hardening-20260811` من `origin/security-hardening-demo-alignment` بعد رفض الدفع إلى الفرع الأصلي بسبب صلاحية GitHub Actions، ثم دُفع commit التقوية `2fb4fd11` بنجاح. بقي `origin/main` عند `8ff3eb6d` ولم يُدمج شيء فيه.

تتكون الحزمة المدفوعة من إصلاحات أمنية واعتمادية واختبارات وتقارير وملفات تشغيل. بعد الدفع لا توجد تغييرات tracked غير ملتزمة؛ توجد فقط patch artifacts محلية غير متتبعة (`.audit/ci-fix.patch` و`.audit/ci-repair.patch`) محفوظة خارج commit لأنها تحتوي whitespace تاريخياً وليست مطلوبة لتشغيل المنصة. لا يوجد worktree ثانٍ ظاهر، ولا توجد إشارة إلى جلسة Git متزامنة أخرى في مساحة العمل؛ ومع ذلك، يجب اعتبار أي ملفات جديدة تظهر بعد هذه النقطة عملاً محتملاً متزامناً وعدم إدراجها تلقائياً.

| التصنيف | الحالة الفعلية | الدليل أو النطاق |
|---|---|---|
| Certified/previous | موجود | commits `a52340f9` و`93ec5a6a` و`7518e742` موثقة كأعمال Wave 3؛ يجب عدم إبطالها |
| Current hardening | committed and pushed | commit `2fb4fd11` على `wave0-audit-hardening-20260811`، ويشمل 52 مساراً |
| Remote branch | منشأ ومدفوع | `origin/wave0-audit-hardening-20260811` عند `2fb4fd11` |
| Source base | محفوظ دون تعديل | `origin/security-hardening-demo-alignment` عند `69035da5` |
| Main | غير مستهدف بالدمج | `origin/main` عند `e1168ffc` وقت آخر تحقق |
| Tags | موجودة | `v1.0.0-RC1`, `v1.0.0-RC2`, `v2.1.0-engineering-factory` |
| Generated local data | مستبعد من Git | `backend/*.db` و`backend.pid` ضمن `.gitignore` |
| Native release | غير متحقق | لا توجد شهادة Android/Windows EXE من هذه البيئة |

## الأسطح الحالية

| السطح | التنفيذ الفعلي | الحالة |
|---|---|---|
| Web | `frontend-v3` React/TypeScript/Vite/PWA مع API client وDashboard shell | منفذ وقابل للبناء؛ لا توجد unit tests فعلية |
| Backend | `backend/app` FastAPI factory، routes، services، models، migrations | واسع؛ اختبارات Backend ناجحة بعد الإصلاحات |
| Android | `mobile/android` Kotlin/Gradle | مصدر موجود؛ build release يحتاج CI/Android SDK كامل |
| Desktop | `mobile/desktop` Flutter | مصدر موجود؛ Windows build غير متحقق هنا |
| Demo | `ENV=demo`, `DEMO_MODE=true`, بيانات اصطناعية و`POST /demo/access` | يعمل محلياً؛ يجب عزله بقاعدة وRedis منفصلين عند النشر |
| Database | PostgreSQL للإنتاج، SQLite للديمو/الاختبارات | Alembic SQLite fresh وصل إلى head؛ PostgreSQL round-trip لم يُثبت هنا |
| Cache/session | Redis مع fallback محدود للبيئات غير الإنتاجية | Redis مشترك مطلوب في الإنتاج |
| Object/storage | Configurations MinIO/S3 موجودة | نشر واستعادة غير متحققين |
| Observability | health, request IDs, timings, metrics, audit and self-healing surfaces | تنفيذ جزئي؛ dashboard/alert drill إنتاجي مطلوب |

## الأسطح deployment وCI

توجد Docker وCompose وKubernetes/Kustomize وHelm وCloudflare وPrometheus/Grafana/Loki/Tempo وRedis Sentinel وPostgreSQL HA وRabbitMQ وMinIO وGitHub Actions. وجود الملفات لا يثبت أن كل مسار منشور أو صالح إنتاجياً. أعمال CI السابقة أصلحت workflows محلياً، لكن صلاحية دفع workflow files أو نجاح GitHub Actions البعيد يجب التحقق بعد الدفع.

## المخاطر المعروفة

ما يزال Wave 4 HARD STOP قائماً للأعمال التدميرية، بما في ذلك حذف فروع `claude/*`، إعادة تسمية `frontend-v3`، حذف ملفات الجذر الحساسة، تغيير سلوك النشر، أو إنشاء GitHub Release. هذه الوثيقة لا تمنح اعتماداً لتلك الأعمال. المخاطر التشغيلية المفتوحة هي PostgreSQL load وRedis HA وbackup/restore وnative builds وغياب unit tests فعلية للواجهة، إضافة إلى 251 تحذيراً غير حاجز في Backend. بعد الدفع، أبلغ GitHub عن 135 تنبيهاً مفتوحاً في default branch، منها 3 حرجة و47 عالية و74 متوسطة و11 منخفضة؛ لم يسمح التكامل بقراءة تفاصيل Dependabot، لذلك تُسجل كخطر supply-chain يحتاج فتح Security/Dependabot في GitHub.

## قرار Wave 0

تمت استعادة الحالة وتحديد العمل المتزامن والحدود، وأُنشئت وثائق Wave 0 السبعة والتحقق منها. دُفعت الحزمة إلى فرع مستقل قابل للمراجعة، ثم توقفت الأعمال الواسعة وفق التوجيه. الدفع إلى فرع التقوية لا يساوي دمجاً في `main` ولا يساوي إصداراً إنتاجياً.
