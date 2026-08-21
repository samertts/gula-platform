# أفضل الممارسات لمنع ثغرات التبعيات العابرة في GULA

## الخلاصة التنفيذية

التبعيات العابرة لا تُدار بإضافة فحص أمني واحد؛ بل بمنظومة تجمع بين **رؤية كاملة لشجرة التبعيات، lockfiles موثوقة، تحديثات صغيرة متكررة، حظر إدخال المخاطر في Pull Requests، وإثبات قابل للتتبع لما دخل صورة الإنتاج**. يقرأ GitHub manifests وlockfiles لاكتشاف التبعيات المباشرة والعابرة، وتساعد lockfiles على تثبيت الإصدارات التي تدخل البناء فعلياً [1].

بالنسبة إلى GULA، القاعدة الأهم هي: **كل artifact إنتاجي يجب أن يُبنى من lockfile محدد، ويُفحص قبل الدمج وبعد البناء، ولا يكفي أن تكون التبعية المباشرة آمنة إذا كان lockfile يسحب نسخة عابرة ضعيفة**.

## 1. ثبّت شجرة التبعيات التي تدخل الإنتاج

يجب اختيار مدير حزم رسمي لكل مسار وعدم ترك CI يختار تلقائياً بين `npm` و`pnpm`. في GULA توجد مسارات متعددة مثل Backend Python، و`frontend-v3`، و`apps/gula-web-suite`، و`mobile-expo`، إضافة إلى manifests جذرية وحزم أخرى. لكل مسار يجب تحديد:

| المسار | المصدر المعتمد للبناء | القاعدة الوقائية |
|---|---|---|
| Backend | `backend/requirements-lock.txt` أو lockfile موحد معتمد | لا تبنِ الإنتاج من حدود دنيا في `requirements.txt` فقط |
| frontend-v3 | مدير واحد وlockfile واحد داخل CI | استخدم `npm ci` أو `pnpm install --frozen-lockfile`، لا تثبيتاً مرناً |
| Web Suite | `apps/gula-web-suite/pnpm-lock.yaml` إذا كان pnpm هو مديره الرسمي | لا تخلط lockfile الجذري مع lockfile التطبيق بلا قرار معماري |
| Mobile Expo | `mobile-expo/package-lock.json` | ثبّت نسخة Node وExpo في CI وأعد بناء lockfile فقط عبر PR |
| Docker/Actions | Dockerfile وملفات workflows المثبتة | ثبّت image digests وAction SHAs عند الإمكان |

يجب فحص أن lockfile محدث مع manifest، وأن CI يفشل عند وجود فرق بينهما. يمنع ذلك حالة شائعة تكون فيها `package.json` آمنة ظاهرياً بينما lockfile القديم يسحب إصداراً عابراً ضعيفاً.

## 2. اجعل التبعيات العابرة مرئية ومراقبة

فعّل Dependency Graph وDependabot alerts لكل مستودع ومسار مدعوم، وتحقق من أن manifests وlockfiles كلها تدخل في الرسم البياني. Dependency Review يعرض التغييرات في التبعيات المباشرة والعابرة داخل lockfiles، وينبه عند إضافة أو تحديث إصدار معروف بالضعف [2].

ينبغي إجراء مراجعة أسبوعية آلية ومراجعة شهرية بشرية لشجرة التبعيات، مع التركيز على:

| إشارة | ما الذي تعنيه | الإجراء |
|---|---|---|
| تبعية عابرة عالية الخطورة | قد تكون داخل runtime حتى لو لم تظهر في manifest المباشر | حدّد الحزمة الأم التي تسحبها، ثم حدّث الأم أو استخدم override مؤقتاً موثقاً |
| تبعية عابرة في development فقط | لا تدخل صورة الإنتاج غالباً، لكن قد تؤثر على CI أو build | افصلها عن runtime وتأكد من عدم نسخها إلى صورة الإنتاج |
| تكرار نسخ الحزمة نفسها | أكثر من إصدار عابر يزيد مساحة الهجوم ويصعّب التصحيح | وحّد النسخ عبر update أو override بعد اختبار التوافق |
| حزمة بلا صيانة أو بلا patch | خطر مستقبلي حتى دون CVE حالية | استبدل التبعية أو اعزلها، ولا تضع exception دائماً |
| lockfile غير مكتشف | GitHub لا يرى كامل graph | صحح manifest/lockfile أو استخدم dependency submission عند الحاجة |

لا تُخفِ المشكلة بإغلاق تنبيه تبعية عابرة لمجرد أنها غير مباشرة. المسؤولية الأمنية تمتد إلى كل ما يُشغّل داخل artifact.

## 3. استخدم lockfiles بطريقة صحيحة

الـlockfile ليس مجرد ملف تثبيت سريع؛ إنه **سجل إصدارات قابل للتدقيق**. يجب حفظه في Git، ومراجعته في كل PR، ومنع تعديله يدوياً إلا لأسباب موثقة. عند تحديث تبعية مباشرة، يجب فحص diff للتأكد من أن التغيرات العابرة متوقعة.

قواعد GULA المقترحة هي:

1. استخدم تثبيتاً deterministic في CI: `npm ci` أو `pnpm install --frozen-lockfile` أو ما يعادلها في Python.
2. امنع البناء إذا كان lockfile غير متزامن مع manifest.
3. لا تستخدم `npm audit fix --force` على `main`، لأنه قد يسبب major upgrades واسعة وغير قابلة للعزل.
4. لا تنسخ بيئة المطور كاملة إلى lockfile؛ حدّث الحزمة المطلوبة مع أقل diff ممكن.
5. افحص `resolved` و`integrity` في lockfiles، ولا تقبل مصادر registry غير معتمدة أو Git URLs غير موثوقة دون مراجعة.
6. أعد بناء artifact من lockfile نفسه، ثم خزّن hash للصورة وSBOM معها.

أوامر تحقق نموذجية:

```bash
# npm
npm ci
npm ls --all
npm audit --audit-level=high

# pnpm
pnpm install --frozen-lockfile
pnpm list --depth Infinity
pnpm audit --audit-level high

# Python
python -m pip check
pip-audit -r backend/requirements-lock.txt
```

## 4. حدّث الحزمة الأم قبل فرض Override

عند ظهور ثغرة في تبعية عابرة، الترتيب المفضل هو:

> **تحديث الحزمة الأم إلى إصدار يصحح الشجرة، ثم استخدام override/resolution مؤقت فقط إذا تعذر ذلك.**

الـoverride مناسب عندما تكون الحزمة الأم بطيئة في الإصلاح أو عندما يكون الإصدار المصحح متوافقاً بشكل مثبت. لكنه قد يكسر API أو يترك الحزمة الأم في حالة لم تختبرها. لذلك يجب أن يتضمن كل override:

| الحقل | المطلوب |
|---|---|
| سبب الإضافة | GHSA/CVE ورقم Dependabot |
| النطاق | الحزمة العابرة والإصدار المفروض |
| اختبار التوافق | المسارات التي شُغلت ونتيجتها |
| المالك | فريق أو شخص مسؤول |
| تاريخ المراجعة | موعد إزالة override أو تحديث الأم |
| خطة التراجع | كيفية العودة إذا فشل runtime |

إذا أصبح override دائماً، فهذا مؤشر إلى ضرورة استبدال الحزمة الأم أو إعادة تصميم المسار، لا إلى ترك الاستثناء بلا نهاية.

## 5. افصل تبعيات الإنتاج عن التطوير

كل تبعية لا تدخل runtime ينبغي أن تكون في development/test scope، وأن يتم البناء من production-only dependencies حيثما يسمح الإطار. هذا لا يلغي أهمية فحصها، لكنه يقلل مساحة الهجوم في الصورة النهائية.

في GULA يجب التأكد من عدم انتقال pytest وlinters وbundler tools إلى صورة backend الإنتاجية، وعدم تضمين devDependencies في artifact frontend إذا كان ذلك غير مطلوب. بعد البناء، افحص محتوى الصورة أو الحزمة:

```bash
# أمثلة عامة؛ عدّلها حسب Dockerfile الفعلي
docker run --rm gula-backend:<tag> python -m pip list
docker run --rm gula-backend:<tag> python -c 'import sys; print(sys.path)'
```

القاعدة الطبية المهمة: **لا يكفي تصنيف الحزمة بأنها development إذا كانت أداة build تشغّل كوداً من حزم غير موثوقة أثناء بناء artifact**. لذلك يجب أيضاً تثبيت CI actions، عزل secrets، وعدم تشغيل PRs غير الموثوقة بامتيازات كتابة.

## 6. اجعل Dependency Review حاجز دمج إلزامياً

أضف workflow على Pull Requests يطبق Dependency Review Action. توثيق GitHub يوضح أن الفحص يستطيع إيقاف PR عند إدخال حزمة ضعيفة، ويمكن ضبطه وفق شدة الثغرة أو license أو scope [3]. مثال أساسي:

```yaml
name: Dependency review

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Dependency review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
```

بعد مرحلة ضبط أولية، يمكن رفع السياسة إلى `moderate` إذا كانت تنبيهات التطوير منخفضة الضجيج، أو استخدام `fail-on-scopes` للتمييز بين production وdevelopment. يجب جعل هذا الفحص required status check على `main`، مع استثناءات أمنية محدودة ومراجعة بشرية.

ينبغي أيضاً تثبيت إصدارات Actions إلى commit SHA موثوق وفق سياسة المستودع، لأن tag المتحرك يضيف مخاطرة مختلفة عن ثغرات npm/Python.

## 7. فعّل تحديثات أمنية صغيرة ومتكررة

فعّل Dependabot security updates وversion updates بجداول منفصلة. تحديثات security يجب أن تعالج CVE/GHSA، بينما version updates تحافظ على حداثة الحزم حتى لا تتراكم القفزات الكبيرة. يمكن استخدام grouping داخل ecosystem واحد لتقليل الضوضاء، لكن لا تجمع تحديثات backend الحساسة مع تحديثات UI أو Mobile في PR واحد.

الإعداد المقترح:

| نوع التحديث | التواتر | الحد الأقصى المقترح |
|---|---:|---:|
| Security updates للإنتاج | يومي أو عند توفر تنبيه | PRs محدودة حسب قدرة المراجعة |
| Version updates للـpatch/minor | أسبوعي | 3–5 PRs لكل ecosystem |
| Major upgrades | شهري ومخطط | PR مستقل مع migration وrollback |
| مراجعة Actions/Docker | أسبوعي | PR مستقل أو مجموعة صغيرة |

الهدف ليس قبول كل PR آلياً، بل منع بقاء الثغرات العابرة حتى تتراكم وتصبح ترقيتها breaking change.

## 8. أضف فحصاً متعدد الطبقات إلى CI/CD

لا تعتمد على أداة واحدة. يوصى بالطبقات التالية:

| الطبقة | ما تفحصه | متى تعمل |
|---|---|---|
| Dependency Review | التغييرات التي يدخلها PR، بما فيها lockfile | كل Pull Request |
| npm/pnpm audit | ثغرات JavaScript المعروفة | PR وnightly |
| pip-audit | حزم Python المقفلة | PR وnightly |
| GitHub Dependabot | graph والتنبيهات المستمرة | مستمر |
| SBOM | ما دخل artifact فعلياً | كل build إنتاجي |
| Image scan | طبقات OS وحزم النظام داخل Docker | قبل registry/production |
| Secret scan | أسرار انكشفت في code أو lockfile | كل push وPR |
| License policy | تراخيص غير مقبولة | كل تغيير تبعية |

يجب أن تكون نتيجة `audit` قابلة للمقارنة مع baseline، لا أن تفشل عشوائياً بسبب كل تحذير منخفض غير متعلق بالإنتاج. أي exception يجب أن يحتوي على رقم CVE/GHSA ومالك وتاريخ انتهاء.

## 9. أنشئ SBOM واثبت مصدر artifact

ولأن lockfile يصف ما يفترض أن يدخل البناء، يجب إنشاء SBOM من artifact نفسه أو من عملية البناء، ثم حفظه مع رقم الإصدار وhash والصورة. يقترح استخدام SPDX أو CycloneDX، وربط SBOM بـcommit وworkflow run.

يمكن تبني ممارسات SLSA تدريجياً؛ إطار SLSA يركز على سلامة artifact، ومصدره، ومنع التلاعب في سلسلة البناء، ويقدم مستويات ضمان متصاعدة [4]. بالنسبة إلى GULA، الأولوية العملية هي:

1. Build من commit معروف داخل CI.
2. منع البناء المحلي كمسار إصدار إنتاجي.
3. توليد provenance وSBOM آلياً.
4. توقيع image/artifact والتحقق منه عند النشر.
5. تسجيل builder وsource revision وdependency lock hash.

هذا لا يمنع CVE وحده، لكنه يضمن أن الفريق يعرف **أي نسخة عابرة دخلت أي artifact وأين يجب إعادة البناء بعد الإصلاح**.

## 10. قلّل مخاطر سلسلة التوريد نفسها

بالإضافة إلى CVEs، يجب التعامل مع خطر package takeover أو typosquatting أو script execution. تطبق GULA الضوابط التالية:

| الضابط | التطبيق |
|---|---|
| registries موثوقة | استخدم npm/PyPI الرسميين أو mirror داخلي موثقاً، ولا تسمح بمصادر عشوائية |
| مراجعة package scripts | راجع `preinstall`, `install`, `postinstall` في الحزم الحساسة |
| صلاحيات CI الدنيا | `GITHUB_TOKEN` بقراءة فقط افتراضياً، ولا تعرض أسراراً لPRs غير موثوقة |
| تثبيت Actions | استخدم SHA أو سياسة مركزية موثوقة |
| منع Git dependencies غير الضرورية | استخدم إصدارات registry قابلة للفحص والتكرار |
| حظر التبعية المهجورة | استبدل الحزم التي لا patch لها أو اعزلها |
| مراجعة المالكين | CODEOWNERS لمسارات lockfiles وworkflows وDocker |
| حماية الفرع | required checks، منع force push، ومراجعة بشرية مزدوجة للتغييرات الحساسة |

## 11. راقب التبعيات بعد النشر

قد تظهر الثغرة بعد بناء صورة الإنتاج، لذلك يجب أن يكون لكل artifact رقم وتاريخ وSBOM. عند صدور GHSA/CVE جديد، يستطيع الفريق البحث عن الحزمة في artifacts المنشورة، ثم تحديد الصور المتأثرة وإعادة بنائها فقط.

ينبغي ربط التنبيهات بـrunbook الحوادث، مع SLA مقترح:

| شدة الثغرة | هدف التقييم | هدف الإصلاح أو التخفيف |
|---|---:|---:|
| حرجة | خلال 4 ساعات | خلال 24 ساعة أو عزل فوري |
| عالية | خلال يوم عمل | خلال 3 أيام عمل |
| متوسطة إنتاجية | خلال 5 أيام عمل | خلال 14 يوماً |
| تطويرية | خلال دورة التحديث التالية | قبل الإصدار التالي |

هذه أهداف تشغيلية داخلية وليست حكماً على قابلية الاستغلال؛ يجب تعديلها بعد معرفة CVSS، exposure، compensating controls، وبيئة GULA.

## 12. سياسة الاستثناءات

لا تستخدم `ignore` أو dismiss كحل دائم. الاستثناء المقبول يجب أن يذكر سبب عدم الانطباق، هل التبعية development-only، هل المسار المتأثر غير مستخدم، وما الضوابط التعويضية. كما يجب تحديد تاريخ انتهاء لا يتجاوز دورة مراجعة قصيرة.

مثال سجل استثناء:

```yaml
exception:
  advisory: GHSA-xxxx-yyyy-zzzz
  dependency: example-transitive-package
  scope: development
  reason: "لا تدخل صورة الإنتاج؛ محصورة في أداة اختبار معزولة"
  compensating_controls:
    - "Dependency Review يمنع إدخال high/critical جديد"
    - "CI يعمل بصلاحيات contents: read"
  owner: platform-security
  expires: 2026-09-15
  review_issue: SEC-1234
```

## 13. اختبارات GULA الخاصة بعد كل تغيير عابر

أي تحديث قد يغير سلوكاً في منصة صحية، لذلك يجب تشغيل اختبارات تتجاوز build العام:

- **Backend:** المصادقة، MFA، RBAC، tenant isolation، CAS، Redis idempotency، FHIR parsing، DHIS2، audit trail، migrations، Webhook HMAC.
- **Wearables:** رفض payload غير الموقع، رفض replay، منع حفظ raw payload، `simulation_only=true`، وإزالة التكرار.
- **AI/Chronic Care:** بقاء `advisory_only=true`، عدم تنفيذ قرار علاجي، ثبات baseline، وتصعيد التنبيه دون spam.
- **Frontend:** TypeScript، build، PWA/offline behavior، عدم تخزين بيانات صحية حساسة في browser cache، والتعامل الآمن مع أخطاء API.
- **Operations:** بناء صورة نظيفة، فحص image، تشغيل smoke tests، قياس latency/error rate، وتجربة rollback.

## 14. خطة تطبيق مختصرة في GULA

| الفترة | الإجراء |
|---|---|
| الآن | تحديد مدير الحزم الرسمي لكل manifest، والتأكد من وجود lockfile داخل كل build |
| هذا الأسبوع | إضافة Dependency Review required check، وتمكين Dependabot لجميع ecosystems الفعلية |
| الجولة التالية | إضافة nightly `pip-audit` و`npm/pnpm audit` مع SBOM artifact |
| خلال دورة الإصدار | فصل production/dev dependencies، وتقليل التكرار، وإزالة Git dependencies غير الضرورية |
| قبل الإنتاج | توقيع images، provenance، CODEOWNERS، branch protection، وrunbook للتنبيه |
| مستمر | تحديثات patch/minor أسبوعية، major upgrades مخططة، ومراجعة شهرية لشجرة التبعيات |

## المبدأ النهائي

أفضل دفاع ضد التبعيات العابرة هو **تقليل المفاجآت**: lockfile ثابت، graph كامل، PR صغير، فحص يمنع الإدخال، artifact موثق، ومراقبة بعد النشر. عندما تكون التبعية العابرة ضعيفة، لا تنتظر تنبيهاً جديداً؛ حدّث الحزمة الأم، أو ثبّت override مؤقتاً بموعد انتهاء، أو استبدل المسار. وفي منصة GULA لا يُسمح بأن تتغلب سرعة التحديث على سلامة المرضى أو سلامة البيانات.

## المراجع

[1]: https://docs.github.com/en/code-security/reference/supply-chain-security/dependency-graph-supported-package-ecosystems "GitHub Docs — Dependency graph supported package ecosystems"

[2]: https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review "GitHub Docs — Dependency review"

[3]: https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/customize-dependency-review-action "GitHub Docs — Customizing dependency review action"

[4]: https://slsa.dev/ "SLSA — Supply-chain Levels for Software Artifacts"
