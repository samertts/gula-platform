# خطة المعالجة الآمنة لتنبيهات Dependabot في GULA

**المستودع:** `samertts/gula-platform`  
**النطاق:** معالجة 8 تنبيهات Dependabot المعلنة على الفرع الرئيسي: 4 عالية و4 متوسطة.  
**الهدف:** إغلاق الثغرات دون إدخال انحدار في خدمات المختبر، المصادقة، FHIR، القياسات الحيوية، Webhook، ومحرك الرعاية المزمنة.

> هذه الخطة لا تعتبر أي تحديث تبعية آمناً لمجرد أن الاختبارات نجحت. في منصة صحية، يجب ربط كل تحديث بمسار استخدام، وتقييم أثره على سلامة البيانات، وخطة تراجع قابلة للتنفيذ.

## 1. الوضع الحالي والقرار الأول

أبلغ GitHub بعد آخر دفع عن ثماني ثغرات في الفرع الافتراضي، لكن تفاصيل الحزم وGHSA/CVE والإصدارات المعالجة لم تكن قابلة للقراءة آلياً بسبب رفض صلاحية Dependabot API (`403 Resource not accessible by integration`). كما أن الفحص المحلي أظهر عدم وجود ثغرات معروفة في `frontend-v3` عبر `npm audit` وفي `backend/requirements-lock.txt` عبر `pip-audit` وقت الفحص. لا ينبغي اعتبار ذلك بديلاً عن سجل GitHub؛ فقد تكون التنبيهات مرتبطة بmanifest آخر، أو بمسار عابر، أو بحالة لم تُحل بعد في الرسم البياني للتبعيات.

القرار الفوري هو **عدم تشغيل `npm audit fix` أو تحديثات شاملة عمياء**، وعدم إغلاق أي تنبيه على أنه false positive قبل توثيق السبب والمالك وتاريخ المراجعة. يجب أولاً استخراج سجل التنبيهات الكامل بصلاحية قراءة Dependabot alerts، ثم ربط كل تنبيه بمسار تبعية وبيئة تشغيل.

## 2. المرحلة الأولى: استخراج سجل التنبيهات وتثبيت خط الأساس

يطلب مالك المستودع أو مسؤول GitHub صلاحية قراءة Dependabot alerts على المستودع. بعد منحها، ينفذ المسؤول الأمر التالي من بيئة موثوقة:

```bash
gh api \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  '/repos/samertts/gula-platform/dependabot/alerts?state=open&per_page=100' \
  --paginate \
  --jq '.[] | {
    number,
    state,
    dependency: .dependency.package.name,
    ecosystem: .dependency.package.ecosystem,
    manifest: .dependency.manifest_path,
    scope: .dependency.scope,
    severity: .security_vulnerability.severity,
    vulnerable_range: .security_vulnerability.vulnerable_version_range,
    first_patched: .security_vulnerability.first_patched_version.identifier,
    ghsa: .security_advisory.ghsa_id,
    cve: .security_advisory.cve_id,
    summary: .security_advisory.summary,
    cvss: .security_advisory.cvss.score
  }' > dependabot-alerts-open.json
```

إذا استمر الخطأ `403`، تُستخرج البيانات من صفحة **Security and quality → Dependabot → Vulnerabilities** في GitHub، أو يطلب مالك المستودع من مسؤول المؤسسة تمكين صلاحية القراءة المناسبة. يجب حفظ نسخة مؤرخة من النتيجة، دون تضمين أسرار أو بيانات مرضى.

بعد ذلك تُنشأ نقطة تراجع محلية قبل أي تعديل:

```bash
cd /home/ubuntu/gula-platform
git fetch origin
git checkout main
git pull --ff-only origin main
git tag -a pre-dependabot-remediation-2026-08-19 \
  -m 'Baseline before Dependabot remediation'
git push origin pre-dependabot-remediation-2026-08-19
```

ويجب تسجيل خط الأساس التالي في تذكرة المعالجة: commit الحالي، صورة الإنتاج الحالية، إصدار Python وNode، نتيجة اختبارات backend، نتيجة build الواجهة، نتيجة `npm audit`، نتيجة `pip-audit`، وحالة migrations.

## 3. المرحلة الثانية: تصنيف التنبيهات الثمانية

لا تُرتب التنبيهات بالـCVSS وحده. توصي GitHub بالاستفادة من ترتيب **Most important** وبتمييز تبعيات الإنتاج عن التطوير، لأن أثر التبعية ومسار استخدامها يدخلان في أولوية المعالجة [1]. يطبق GULA التصنيف التالي:

| التصنيف | معيار التصنيف | الإجراء |
|---|---|---|
| P0 عاجل | تبعية تشغيلية عالية أو ثغرة قابلة للاستغلال عن بعد، خصوصاً في HTTP، المصادقة، التشفير، parsing، أو رفع الملفات | فرع مستقل فوراً، تحديث إلى أول إصدار مصحح، اختبار مكثف، ونشر staging سريع |
| P1 مرتفع | تبعية إنتاجية عالية لكن الاستغلال يتطلب شروطاً إضافية أو مساراً غير مكشوف مباشرة | معالجة خلال أقرب نافذة إصدار، مع اختبار مسار الاستخدام والـrollback |
| P2 متوسط إنتاجي | تبعية تشغيلية أو عابرة ذات أثر محدود أو تعويضات أمنية قائمة | إدراجها في PR مخصص حسب ecosystem، وعدم تأجيلها بلا مالك وتاريخ |
| P3 متوسط تطويري | أداة اختبار أو بناء لا تدخل صورة الإنتاج | تحديث منضبط، مع منع انتقالها إلى runtime، ثم إغلاق التنبيه بعد CI ناجح |

لكل تنبيه يجب تسجيل: رقم التنبيه، GHSA/CVE، الحزمة، الـecosystem، manifest، direct/transitive، production/development، الإصدار المتأثر، أول إصدار مصحح، هل يتطلب major upgrade، هل تستعمل GULA المسار المتأثر، وإجراء التخفيف المؤقت.

## 4. المرحلة الثالثة: مطابقة التنبيه مع بنية GULA

يحتوي المستودع على أكثر من عائلة manifests، ولذلك لا يجوز تحديث lockfile واحد والافتراض أن جميع البيئات أصبحت آمنة. المسارات التي يجب فحصها هي:

| البيئة | الملفات/المسارات التي يجب فحصها | أمر التحقق الأساسي |
|---|---|---|
| Backend Python | `backend/requirements.txt`, `backend/requirements-lock.txt`, `backend/pyproject.toml` | `pip-audit -r backend/requirements-lock.txt -f json` |
| الواجهة الرئيسية | `frontend-v3/package.json`, `frontend-v3/package-lock.json`, `frontend-v3/pnpm-lock.yaml` | `npm audit --json` بعد تثبيت الأداة المعتمدة في CI |
| مستودع JavaScript الجذري | `package.json`, `package-lock.json`, `pnpm-lock.yaml` | `npm audit` أو `pnpm audit` وفق أمر CI، لا كلاهما عشوائياً |
| Web Suite | `apps/gula-web-suite/package.json`, `pnpm-lock.yaml` | `pnpm audit --json` |
| Mobile Expo | `mobile-expo/package.json`, `package-lock.json` | `npm audit --json`, `npm run typecheck`, `npm test` |
| تطبيقات/حزم أخرى | `apps/*`, `packages/*`, `platform/*` التي تحتوي manifests | فحص كل manifest في workflow مستقل |
| GitHub Actions | `.github/workflows/*.yml` | مراجعة كل `uses:` وتحديث action إلى commit SHA مصحح |

يجب أولاً تحديد أداة التثبيت الرسمية لكل مسار من CI. وجود `package-lock.json` و`pnpm-lock.yaml` لنفس التطبيق لا يعني أنهما متكافئان؛ يجب اختيار مدير حزم واحد لكل build، أو إبقاء lockfiles متزامنة صراحةً إن كان CI يدعم الاثنين. لا ينبغي تنفيذ تحديثات متوازية على lockfiles مختلفة من دون معرفة أي واحد يدخل صورة الإنتاج.

أوامر تحديد ما إذا كانت الحزمة مباشرة أو عابرة:

```bash
# npm
npm ls <PACKAGE> --all
npm explain <PACKAGE>

# pnpm
pnpm why <PACKAGE>
pnpm list <PACKAGE> --depth Infinity

# Python
python3 -m pip show <PACKAGE>
pipdeptree --reverse --packages <PACKAGE> 2>/dev/null || true
```

## 5. المرحلة الرابعة: معالجة تبعيات Python

يجب أن تكون صورة الإنتاج مبنية من `backend/requirements-lock.txt` أو من آلية lock موحدة ومراجعة، لا من `requirements.txt` ذي الحدود الدنيا وحده. قبل رفع إصدار حزمة، يحدد الفريق هل التحديث direct أم transitive، وهل يغير FastAPI/Starlette أو SQLAlchemy أو cryptography أو حزم المصادقة. هذه التبعيات لا تُجمع في PR واحد إذا كان التغيير قد يبدل سلوكاً أمنياً أو قاعدة بيانات.

الطريقة الآمنة هي إنشاء فرع لكل عائلة عالية الأثر، تحديث الحزمة إلى **أول إصدار مصحح** أو إصدار ضمن نطاق التوافق، ثم إعادة توليد lockfile بطريقة قابلة للتكرار. لا يُستخدم `pip install --upgrade` على بيئة العمل ثم نسخ كل الناتج إلى lockfile؛ فهذا قد يرفع عشرات الحزم غير المرتبطة ويصعب تحديد سبب الانحدار.

مثال سير عمل مضبوط، مع استبدال `<PACKAGE>` و`<FIXED_VERSION>` بالقيم الموجودة في سجل Dependabot:

```bash
git switch -c security/dependabot-python-<package>
python3 -m venv /tmp/gula-dependabot-venv
. /tmp/gula-dependabot-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-lock.txt
python -m pip install '<PACKAGE>==<FIXED_VERSION>'
python -m pip check
pip-audit -r backend/requirements-lock.txt
```

بعد ذلك يُحدّث المصدر المعتمد للـlockfile بأداة المشروع، ويُراجع diff للتأكد من أن التغيير لا يبدل حزماً غير مرتبطة. إذا كان التنبيه عابراً، يجب تحديث الحزمة الأم أو تثبيت override/constraint موثق، ثم إثبات أن الحزمة العاجزة لم تعد موجودة في dependency tree. يجب عدم استخدام override دائم من دون issue توضح سبب وجوده وموعد إزالته.

بالنسبة إلى حزم التشفير والمصادقة وJWT وparsing، يجب إضافة اختبارات regression خاصة بـGULA، تشمل: توقيع JWT والتحقق من رفض التلاعب، HMAC للـWebhook، كلمات المرور وMFA، TLS/client behavior، parsing للمدخلات غير الصالحة، وعدم تسريب تفاصيل الاستثناء. بالنسبة إلى SQLAlchemy/Alembic/psycopg، يجب تشغيل migrations من قاعدة فارغة ومن snapshot اختبار، ثم فحص single head وround-trip.

## 6. المرحلة الخامسة: معالجة تبعيات npm وpnpm

تحديثات JavaScript يجب أن تكون موجهة. يبدأ الفريق بتحديث الحزمة المباشرة أو الأم المطلوبة إلى أول إصدار مصحح، ثم يعيد إنشاء lockfile فقط في مسار التطبيق المعني. لا يُنصح بتشغيل `npm audit fix --force` على الفرع الرئيسي؛ لأنه قد ينفذ major upgrades ويغير runtime أو bundler أو React/Vite دون مراجعة.

مثال لـ`frontend-v3`:

```bash
cd frontend-v3
git switch -c security/dependabot-<package>
npm ci
npm ls <PACKAGE> --all
npm install --package-lock-only <PACKAGE>@<FIXED_VERSION>
npm ci
npm audit --audit-level=high
npm run build
```

إذا كان CI يستخدم pnpm في هذا المسار، يستخدم الفريق بدلاً من ذلك:

```bash
pnpm install --frozen-lockfile
pnpm why <PACKAGE>
pnpm update <PACKAGE>@<FIXED_VERSION> --lockfile-only
pnpm install --frozen-lockfile
pnpm audit --audit-level high
```

يجب تشغيل الاختبارات الخاصة بالمسار، ثم اختبارات الأمن التي تعتمد على الحزمة. بالنسبة إلى تطبيقات `gula-web-suite` و`mobile-expo`، تُعالج كل بيئة في PR مستقل إذا كان لها runtime أو release pipeline مستقل. يجب فحص تأثير التحديث على PWA service worker، routing، offline cache، WebCrypto، رفع الملفات، وواجهات API؛ ولا يجوز تخزين بيانات صحية حساسة في cache جديد لمجرد أن الحزمة المحدثة قدمت آلية caching.

## 7. المرحلة السادسة: فحص GitHub Actions وسلسلة البناء

قد تكون بعض التنبيهات مرتبطة بحزم Actions أو صور البناء. يجب مراجعة كل سطر `uses:`، تحديث الـAction إلى إصدار مصحح، ثم تثبيته إلى commit SHA موثوق بدلاً من tag متحرك متى كان ذلك متوافقاً مع سياسة المستودع. يجب فحص Docker base images، أدوات kubectl، Node/Python setup، وعمليات upload/download artifacts.

يجب منع workflows من تشغيل كود غير موثوق بامتيازات كتابة على `main`. وتُراجع صلاحيات `GITHUB_TOKEN` لتكون `contents: read` افتراضياً، مع منح `id-token` أو `packages` أو `security-events` فقط للخطوات التي تحتاجها. أي تغيير في workflow أمني يجب أن يمر بمراجعة بشرية من مالك المستودع، لا بموافقة تلقائية من Dependabot فقط.

## 8. تقسيم Pull Requests المقترح

لتقليل مساحة الانفجار، يقترح تقسيم العمل إلى PRs صغيرة بدلاً من PR واحد للثغرات الثمانية:

| PR | النطاق | سبب الفصل |
|---|---|---|
| PR-1 | أعلى تنبيه إنتاجي في Backend | يحتوي على أثر سريري/أمني محتمل ويحتاج مراجعة عميقة |
| PR-2 | باقي تبعية Backend العابر أو الأمني | عزل تغيرات Python والـlockfile |
| PR-3 | `frontend-v3` | بناء الواجهة وPWA واختبارات TypeScript مستقلة |
| PR-4 | `gula-web-suite` أو root JavaScript | منع خلط lockfiles ومسارات نشر مختلفة |
| PR-5 | Mobile أو GitHub Actions | فصل build المحمول وصلاحيات CI |
| PR-6 | Dependency Review وDependabot configuration | تحسين الوقاية لا خلطها مع إصلاح runtime |

يمكن دمج تنبيهات منخفضة المخاطر من نفس ecosystem في PR واحد، لكن لا ينبغي جمع تحديثات cryptography/auth/database مع تحديثات UI أو أدوات التطوير. توصي GitHub بأن Dependabot security updates ينشئ PRs تلقائياً عندما يتوفر إصدار مصحح، وأن security updates تختلف عن version updates؛ كما أن `dependabot.yml` يخصص سلوك Dependabot ولا يغلق التنبيهات بذاته [2] [3].

## 9. ضوابط CI الإلزامية لكل PR

قبل الدمج، يجب أن يمر PR على مراحل متسلسلة:

```bash
# Backend
python3 -m compileall -q backend/app backend/tests
cd backend && alembic heads && cd ..
PYTHONPATH="$PWD/backend" pytest backend/tests -q
pip-audit -r backend/requirements-lock.txt

# frontend-v3؛ استخدم مدير الحزم المعتمد في CI
npm --prefix frontend-v3 ci
npm --prefix frontend-v3 audit --audit-level=high
npm --prefix frontend-v3 run build
```

ويضاف إلى ذلك اختبار fresh database، migration upgrade/downgrade أو round-trip حسب سياسة المشروع، اختبارات tenant isolation، CAS، idempotency، Webhook signing، `simulation_only`, `advisory_only`, FHIR contracts، وRBAC. يجب ألا يكتفي CI بمؤشر `npm audit`؛ لأن الإصلاح يجب أن يثبت سلامة الاستخدام الفعلي.

يوصى بإضافة **Dependency Review Action** إلى Pull Requests لمنع إدخال تبعية عالية الخطورة أو ترخيص غير مقبول. هذه الآلية تفحص فرق التبعيات في PR وتستطيع إيقافه عند اكتشاف مشكلات، وهي مكملة وليست بديلاً عن Dependabot alerts [4] [5].

## 10. الاختبار السريري والتشغيلي بعد نجاح CI

بعد نجاح CI، تُبنى صورة staging جديدة بتوقيع ومصدر قابل للتتبع، ثم تُنشر في staging فقط. قبل أي canary، تُنفذ اختبارات smoke على: تسجيل الدخول وMFA، إنشاء طلب مخبري، إدخال نتيجة، تحديث CAS متعارض، FHIR read/search، DHIS2 aggregate، Redis idempotency، wearable measurement، Webhook HMAC، baseline advisory، وتنبيهات chronic care.

تُراجع مؤشرات: error rate، latency p50/p95/p99، معدلات 4xx/5xx، أخطاء Redis/PostgreSQL، فشل migrations، رسائل Sentry، duplicate events، وعدم وجود تغير في audit trail. يجب أن تكون خطة الرجوع هي إعادة صورة الإصدار السابق، وليس إزالة التبعية يدوياً من بيئة حية.

إذا كان مسار النشر يستخدم canary، يبدأ بنسبة صغيرة مثل 10% ثم يرفع تدريجياً فقط عند استقرار المؤشرات. يجب أن تشمل نافذة المراقبة على الأقل دورة مراقبة تشغيلية كاملة لكل خطوة، مع rollback تلقائي أو يدوي موثق عند تجاوز عتبة الخطأ أو ظهور أثر سريري غير متوقع.

## 11. إغلاق التنبيه أو قبول المخاطر

لا يُغلق التنبيه إلا في إحدى الحالات التالية: تم دمج إصلاح مصحح وأصبح GitHub يعيد تقييمه كمغلق؛ أو ثبت أن التبعية غير مستخدمة/غير قابلة للوصول وتم حذفها؛ أو يوجد سبب موثق لقبول المخاطر مع تعويض أمني ومالك وتاريخ انتهاء ومراجعة قانونية/أمنية مناسبة. يجب تجنب خيار `dismiss` بسبب “لا وقت” أو “اختبار محلي ناجح”.

بالنسبة إلى تنبيه عالٍ بلا patch متاح، يوثق الفريق: المسار المتأثر، إمكانية الاستغلال، سبب عدم الانطباق أو التعويض، WAF/rate limit/segmentation المؤقت، المالك، تاريخ المراجعة، وخطة الترقية أو الاستبدال. في منصة صحية، قبول الخطر يجب أن يكون استثناءً مؤقتاً لا بديلاً عن الإصلاح.

## 12. الوقاية بعد إغلاق التنبيهات

يضاف `.github/dependabot.yml` ليغطي كل ecosystem فعلي، مع جداول تحديث منفصلة وحد أقصى معقول للـPRs. مثال أولي قابل للتعديل بعد التأكد من أن كل directory صحيح:

```yaml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5

  - package-ecosystem: npm
    directory: /frontend-v3
    schedule:
      interval: weekly
    open-pull-requests-limit: 5

  - package-ecosystem: npm
    directory: /mobile-expo
    schedule:
      interval: weekly
    open-pull-requests-limit: 3

  - package-ecosystem: npm
    directory: /apps/gula-web-suite
    schedule:
      interval: weekly
    open-pull-requests-limit: 5

  - package-ecosystem: pip
    directory: /backend
    schedule:
      interval: weekly
    open-pull-requests-limit: 5

  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
```

يجب مراجعة هذه التهيئة قبل اعتمادها لأن Dependabot security updates تعتمد على manifests وlockfiles المدعومة، ولأن configuration لا يغني عن تمكين dependency graph وDependabot alerts/security updates في إعدادات المستودع [2] [3]. يمكن إضافة grouping للتحديثات الأمنية داخل ecosystem واحد، لكن لا ينبغي تجميع ecosystems مختلفة أو تغييرات حساسة معاً. كما يجب وضع CODEOWNERS لمسارات `.github/workflows`, `backend/requirements*`, وlockfiles، وإلزام مراجعة أمنية ومسار CI ناجح.

## 13. معيار الإغلاق النهائي للثغرات الثمانية

يُعتبر العمل مغلقاً فقط عند تحقق جميع الشروط التالية:

| الشرط | الدليل المطلوب |
|---|---|
| معرفة كل تنبيه | export مؤرخ يتضمن GHSA/CVE والحزمة والmanifest |
| معالجة الأربع العالية | PRs مدمجة أو قبول خطر موثق بموافقة مالك أمني |
| معالجة الأربع المتوسطة | PRs مدمجة أو استثناء مؤقت له تاريخ انتهاء |
| سلامة lockfiles | diff محدود وقابل لإعادة البناء، دون تغييرات غير مفسرة |
| نجاح الاختبارات | backend، كل frontend/mobile relevant، وsecurity regression |
| سلامة قاعدة البيانات | migration checks وfresh/upgrade/rollback evidence |
| سلامة التشغيل | staging smoke وcanary/rollback evidence |
| استمرار العزل والتدقيق | tenant isolation، RBAC، audit، CAS، idempotency |
| الوقاية | Dependabot configuration، dependency review، CODEOWNERS، schedule |
| إعادة الفحص | GitHub يعيد تقييم التنبيهات ويظهر عدم وجود open high alerts غير مبررة |

## 14. الترتيب الموصى به لفريق GULA الآن

أولاً، الحصول على صلاحية قراءة Dependabot alerts واستخراج تفاصيل التنبيهات الثمانية. ثانياً، معالجة التنبيه العالي الذي يطال production runtime أو parsing/auth/crypto، مع PR مستقل واختبارات regression. ثالثاً، معالجة بقية Backend ثم `frontend-v3` ثم بقية تطبيقات JavaScript وActions حسب الـmanifest الفعلي. رابعاً، إضافة dependency review وتهيئة Dependabot بعد التأكد من مسارات CI. خامساً، تنفيذ staging ثم canary مع rollback، وإغلاق التنبيهات فقط بعد أن يعيد GitHub تقييمها.

لا يُنصح بترقية كل التبعيات إلى أحدث إصدار في نفس الجولة؛ الهدف هو **أقل تغيير يزيل الثغرة مع الحفاظ على السلوك**. بعد الإغلاق، يمكن تنفيذ دورة version updates منفصلة ومجدولة، لأن تحديثات الإصدار العامة تختلف عن security updates ولا ينبغي خلطها مع إصلاحات الثغرات الحرجة [2].

## المراجع

[1]: https://docs.github.com/code-security/dependabot/dependabot-alerts/viewing-and-updating-dependabot-alerts "GitHub Docs — Viewing and updating Dependabot alerts"

[2]: https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-security-updates "GitHub Docs — Dependabot security updates"

[3]: https://docs.github.com/code-security/reference/supply-chain-security/dependabot-options-reference "GitHub Docs — Dependabot options reference"

[4]: https://docs.github.com/en/code-security/how-tos/secure-your-software-supply-chain/manage-your-dependency-security/configure-dependency-review-action "GitHub Docs — Configuring the dependency review action"

[5]: https://github.com/actions/dependency-review-action "GitHub — Dependency Review Action"
