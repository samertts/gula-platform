# GULA Command 09 — Authoritative Baseline

**التاريخ:** 2026-08-17 (GMT+3)
**المستودع:** `samertts/gula-platform`
**الغرض:** تثبيت الحالة الفعلية قبل P0/P4 reconciliation، مع الفصل الصريح بين الدليل المحلي، والدليل الخارجي، وما بقي غير قابل للتحقق.

> هذه الوثيقة baseline وليست إعلاناً عن جاهزية الإنتاج. نجاح اختبارات محلية جزئية لا يحوّل طبقات CI أو PostgreSQL أو native أو deployment غير القابلة للتحقق إلى `PASS`.

## 1. Git والفرع والحالة المحلية

| العنصر | القيمة الفعلية | التصنيف | الدليل |
|---|---|---|---|
| الفرع الحالي | `chore/security-ddos-hardening-clean` | `PASS` محلياً | `git branch --show-current` |
| HEAD المحلي | `478bad1f927543323236c98da5cbb6e0a123dc40` (`test: close identity lifecycle evidence gaps`) | `PASS` محلياً | `git rev-parse HEAD` |
| origin للفرع الحالي | يطابق `478bad1f927543323236c98da5cbb6e0a123dc40` | `PASS` | `git ls-remote origin refs/heads/chore/security-ddos-hardening-clean` |
| origin/main | `1e07b8d677c5f7c94d0fb387937eff959af9589d` | `PASS` كقراءة Git | `git ls-remote origin refs/heads/main` |
| state drift | `origin/main != HEAD`; تغييرات Commands 01–08 موجودة على PR #226 ولم تُدمج في main | `DRIFT_CONFIRMED` | مقارنة SHA وPR metadata |
| working tree | نظيف وقت baseline | `PASS` | `git status --short` بلا مخرجات |
| commits الأخيرة | Commands 04–08 وامتداداته الأمنية موجودة في فرع PR الحالي | `PASS` كحالة فرع | `git log --oneline -8` |

النتيجة العملية هي أن أي مسار يعتمد على `main` أو deployment متصل تلقائياً بـ`main` لا يمكن اعتباره ممثلاً لـHEAD الحالي. لا يجوز وصف فرع PR بأنه production-aligned لمجرد أن Vercel أنشأ deployment metadata له.

## 2. Pull requests ذات الصلة

الـPR الحالي هو **#226** بعنوان `security: harden headers and add shared DDoS rate limiting` وهو مفتوح ومبني على `main`. PR **#227** الخاص ببوابات ما قبل P5 مفتوح أيضاً. كما أن PRs **#225** و**#223** و**#222** و**#220** مفتوحة، بينما PR **#224** و**#216** و**#214** و**#203** مغلقة وغير مدمجة وفق الحالة التي قُرئت في baseline. من الـPRs المرتبطة التي ظهرت كمُدمجة: **#221، #219، #218، #217، #215، #213، #212، #211، #210، #209، #208، #207، #206، #205، #204، #202، #201، #200، #199، #198**.

لا يُستنتج من حالة `MERGED` أو من وجود check run أن الموافقات البشرية الأمنية أو التشغيلية أو القانونية قد تمت. كما لا يُسمح لهذا الأمر بدمج أي PR تلقائياً.

## 3. CI وGitHub Actions

على HEAD `478bad1f` ظهرت **17 workflow runs** بحالة `completed/failure`. فحص job metadata للعينات وجميع الوظائف ذات الصلة أظهر النمط نفسه: `runner_id: 0`، واسم runner فارغ، و`steps: 0`، وفشل خلال ثوانٍ قليلة من وقت الإنشاء، مع غياب logs قابلة للتحليل. شمل ذلك بوابات backend وIAM وsecurity وCodeQL وquality وformatting وfrontend E2E/PWA وmobile Android/iOS وFlutter وPreview Deploy.

| ملاحظة CI | الاستنتاج الصحيح |
|---|---|
| كل jobs الفاشلة التي فُحصت لها `runner_id=0` و`steps=0` | فشل بنية تنفيذ خارجية قبل بدء خطوات workflow |
| لا توجد خطوة checkout أو install أو test في job metadata | لا توجد أدلة على فشل source-code داخل هذه runs |
| نتائج GitHub ظاهرة كـ`failure` | لا تُحوّل إلى `PASS`، لكنها تُصنّف `BLOCKED_EXTERNAL` عند غياب runner/logs |
| التحقق المحلي للـbackend/frontend ناجح | يفصل code evidence المحلي عن CI availability ولا يستبدل CI المفقود |

**قرار baseline:** CI الحالي **`BLOCKED_EXTERNAL`** وليس source failure مثبتاً. إصلاحه يتطلب صلاحية بشرية على GitHub Actions/runner policy أو billing أو repository execution settings؛ لا يجوز تعطيل gates أو suppress failures أو حذف tests كحل.

## 4. Vercel

موصل Vercel موجود ومفعّل بوضع القراءة التي استُخدمت في baseline السابق. المشروع هو `gula-platform` ومعرّفه `prj_xvgrHcfO6BWlwViUJ6HRQdawPsKX`. إعدادات الحماية المقروءة هي:

| إعداد الحماية | القيمة | التصنيف |
|---|---|---|
| SSO/Vercel Authentication | مفعّل، `all_except_custom_domains` | `PASS` كإعداد حماية مقروء |
| Password protection | غير مفعّل | `PASS` كقراءة، لا يعني جاهزية |
| Trusted IPs | غير مفعّل، قائمة العناوين فارغة | `PASS` كقراءة |
| أحدث deployment مقروء | `dpl_94iGV1XhgmrA2Lrfy7GJeX3oMHJf`، مرتبط بفرع PR #226 وبـcommit `478bad1f`، وحالته `BLOCKED` | `BLOCKED_EXTERNAL` |
| deployment الحالي لـHEAD `478bad1f` | موجود metadataياً لكنه `BLOCKED` وغير قابل للاستخدام كـlive evidence | `BLOCKED_EXTERNAL` |

لم تُعطّل SSO، ولم يُنشأ deployment، ولم تُنشأ temporary access link، ولم تُغيّر حماية Vercel. وجود project أو deployment metadata وحده لا يثبت backend runtime أو PostgreSQL أو production readiness.

## 5. Railway وbackend runtime وPostgreSQL

لا يوجد Railway connector في إعدادات الجلسة، ولا Railway CLI، ولا PostgreSQL/`psql` محلياً، ولا Docker runtime. لا يوجد live backend على المنفذ المحلي المعتاد؛ الموجود وقت الفحص هو Vite على `127.0.0.1:5173` فقط.

ملف `.github/workflows/deploy.yml` يصف نموذج تحقق يدوي read-only من health endpoint بعد deployment تلقائي متوقع من `main`. لذلك فإن مقارنة `origin/main` المتأخر مع HEAD الخاص بالـPR تثبت وجود فجوة بين فرع العمل ومسار النشر المتوقع، لكنها لا تثبت أن Railway متوقف أو أن قاعدة البيانات تالفة.

| طبقة الإنتاج | الحالة في baseline | سبب التصنيف |
|---|---|---|
| commit الذي يمثل main | `1e07b8d6`، مختلف عن HEAD | `DRIFT_CONFIRMED` |
| CI لهذا HEAD | runner failure قبل الخطوات | `BLOCKED_EXTERNAL` |
| Vercel deployment | حماية SSO تمنع التحقق العام، وآخر deployment مقروء `BLOCKED` | `BLOCKED_EXTERNAL` |
| Railway service/runtime | لا connector ولا live read-only evidence | `UNVERIFIED` |
| PostgreSQL live/staging | لا اتصال ولا `psql` ولا Docker | `UNVERIFIED` |
| migration state في قاعدة البيانات الفعلية | غير مقروء | `UNVERIFIED` |
| production environment values | غير مقروء | `UNVERIFIED` |

## 6. Alembic والمخطط

أظهر `alembic heads` رأساً واحداً هو **`20260816_0023`**، ووالده `20260815_0022`. يتضمن التاريخ نقاط دمج سابقة عند `20260815_0003` و`20260815_0015` لكنه ينتهي برأس واحد، ولا توجد في baseline علامة على multiple heads. rehearsal offline للترقية من `20260815_0022` إلى `20260816_0023` وللرجوع العكسي أُنجز محلياً بنجاح في الأدلة السابقة.

| فحص قاعدة البيانات | الحالة |
|---|---|
| single Alembic head | `PASS` محلياً |
| migration graph source-level | `PASS` من حيث وجود رأس واحد ومسار متصل |
| offline upgrade | `PASS` |
| offline downgrade | `PASS` |
| apply على PostgreSQL حقيقية | `UNVERIFIED` |
| rollback مع existing data/isolation/locks | `UNVERIFIED` |
| أي DDL في production | لم يُنفّذ |

## 7. Feature flags وruntime defaults

القيم التالية هي defaults التي يفرضها مصدر `backend/app/config.py` عند غياب env overrides. لا يجوز تسميتها live production values قبل قراءة runtime الفعلي.

| التحكم | default المصدر | المعنى الأمني |
|---|---:|---|
| `PUBLIC_SELF_REGISTRATION_ENABLED` | `false` | لا تسجيل عام؛ onboarding يمر عبر المسارات المعتمدة |
| `ENABLE_API_DOCS` | `false` | لا تفعيل تلقائي لوثائق API في الإنتاج |
| `ACCOUNT_RECOVERY_EMAIL_ENABLED` | `false` | provider delivery غير مُثبت، والاستعادة fail-closed/manual-review |
| `ACCOUNT_RECOVERY_MANUAL_REVIEW_ENABLED` | `true` | العمليات عالية الخطورة تتوقف عند `PENDING_REVIEW` |
| `SNDHS_ENABLE_NATIONAL_ID` | `false` | لا تفعيل لهوية وطنية عبر default |
| `GULA_ADAPTER_MODE` | `stub` | adapters الخارجية لا تعمل live افتراضياً |
| `GULA_ADAPTER_MODE_NID` | يرث `stub` | لا ربط حكومي فعلي افتراضياً |
| `ENABLE_FINANCIAL_ENGINE` | `false` | المحرك المالي feature-gated ومغلق افتراضياً |
| `ENABLE_ADS` | `false` | الإعلانات مغلقة افتراضياً |

مصدر الإعدادات يفرض كذلك أن staging يتطلب صراحة `CORS_ORIGINS` و`TRUSTED_HOSTS`، وأن production/staging لا ينبغي أن يعملا بإعدادات degraded. هذه حواجز source-level، لكنها لا تثبت أن env الفعلي في Railway يطابقها.

## 8. State Drift inventory

| المجال | الحالة | ملاحظة |
|---|---|---|
| Git branch مقابل `origin/main` | drift مثبت | PR #226 غير مدمج |
| Git مقابل GitHub CI | drift/blocked | CI فشل قبل بدء الخطوات |
| Git مقابل Vercel | drift/blocked | deployments المقروءة أقدم من HEAD ومحميّة/blocked |
| Git مقابل Railway | غير قابل للمقارنة | لا read-only connector أو runtime evidence |
| Git مقابل PostgreSQL | غير قابل للمقارنة | لا اتصال live/staging |
| source defaults مقابل production env | لا يمكن إثبات التطابق | env runtime غير مقروء |
| local tests مقابل production readiness | لا تكافؤ | الاختبارات المحلية دليل code-level فقط |

## 9. Baseline decision

الحالة السلطوية قبل reconciliation هي **`P0_RECONCILIATION_REQUIRED`** مع blockers خارجية واضحة، وليست `P0_COMPLETE` أو `P0_CANDIDATE_FOR_CLOSURE`. تظل P4 بحاجة إلى Acceptance Matrix رسمية وأدلة لكل صف، وتظل P5 صراحة:

> **`P5_BLOCKED_BY_PREREQUISITE`** حتى يثبت `P4_COMPLETE` مع Governance Authorization.

## المراجع

[1]: `../backend/app/config.py` — runtime guards والـfeature flags الافتراضية.
[2]: `../.github/workflows/deploy.yml` — نموذج تحقق Railway القائم على `main`.
[3]: `command05-account-recovery-hardening-report.md` — recovery/session/provider/migration evidence.
[4]: `command06-authorization-context-hardening-report.md` — membership/workspace/authorization/audit evidence.
[5]: `command07-08-identity-lifecycle-closure-report.md` — Web/PWA/native/CI/Vercel evidence السابقة.
[6]: `../frontend-v3/vercel.json` — intended headers/rewrites؛ لا يثبت live deployment behavior.
[7]: GitHub Actions run metadata for HEAD `478bad1f` — محفوظ في terminal evidence الخاص بالجلسة، jobs ذات `runner_id=0` و`steps=0`.
[8]: Vercel read-only results — `list_deployments` و`get_project_deployment_protection` الحاليان محفوظان في `.mcp/tool-results/` ضمن هذه الجلسة، وأحدث HEAD deployment هو `dpl_94iGV1XhgmrA2Lrfy7GJeX3oMHJf` بحالة `BLOCKED`.
