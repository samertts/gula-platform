# GULA — Current Repository State

**تاريخ الاستعادة:** 11 أغسطس 2026

**المستودع:** [samertts/gula-platform](https://github.com/samertts/gula-platform)

**الفرع الحالي:** `security-hardening-demo-alignment`

**HEAD المحلي:** `2de4932ef33aa104a1b8385a8d5df5391acf351b`

## الحالة التنفيذية

المستودع ليس فارغاً، ويحتوي على Backend واسع مبني على FastAPI وSQLAlchemy/Alembic، واجهة React/Vite حديثة في `frontend-v3`، مسارات واجهة أقدم، Android/Kotlin، Flutter Desktop، ومجموعة كبيرة من خدمات التكامل والبنية التحتية. الفرع المحلي متقدم عن `origin/security-hardening-demo-alignment` بعمل محلي لم يُرفع بعد، بينما `origin/main` عند `8ff3eb6d` وفق الاستعادة الحالية.

العمل staged محلياً يتكون من إصلاحات أمنية واعتمادية واختبارات وتقارير وملفات تشغيل. لا توجد تغييرات unstaged وقت إنشاء هذه الوثيقة. لا يوجد worktree ثانٍ ظاهر، ولا توجد إشارة إلى جلسة Git متزامنة أخرى في مساحة العمل؛ ومع ذلك، يجب اعتبار أي ملفات جديدة تظهر بعد هذه النقطة عملاً محتملاً متزامناً وعدم إدراجها تلقائياً.

| التصنيف | الحالة الفعلية | الدليل أو النطاق |
|---|---|---|
| Certified/previous | موجود | commits `a52340f9` و`93ec5a6a` و`7518e742` موثقة كأعمال Wave 3؛ يجب عدم إبطالها |
| Current hardening | staged محلياً | 47 مساراً تشمل الأمن، startup، migrations، tests، scripts، وتقارير |
| Remote branch | لم يتلقَ هذه الحزمة بعد | `origin/security-hardening-demo-alignment` عند `69035da5` |
| Main | غير مستهدف بالدمج | `origin/main` عند `8ff3eb6d` |
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

ما يزال Wave 4 HARD STOP قائماً للأعمال التدميرية، بما في ذلك حذف فروع `claude/*`، إعادة تسمية `frontend-v3`، حذف ملفات الجذر الحساسة، تغيير سلوك النشر، أو إنشاء GitHub Release. هذه الوثيقة لا تمنح اعتماداً لتلك الأعمال. المخاطر التشغيلية المفتوحة هي PostgreSQL load وRedis HA وbackup/restore وnative builds وغياب unit tests فعلية للواجهة، إضافة إلى 251 تحذيراً غير حاجز في Backend.

## قرار Wave 0

تمت استعادة الحالة وتحديد العمل staged والحدود. يسمح ذلك بإنشاء تقارير Wave 0 السبعة والتحقق منها، ثم التوقف وفق التوجيه قبل أي تنفيذ واسع. الدفع إلى فرع التقوية لا يساوي دمجاً في `main` ولا يساوي إصداراً إنتاجياً.
