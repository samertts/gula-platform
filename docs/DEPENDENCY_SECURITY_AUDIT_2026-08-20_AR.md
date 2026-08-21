# تقرير التدقيق الأمني الشامل للتبعيات — GULA

**التاريخ:** 20 أغسطس 2026
**المستودع:** [samertts/gula-platform](https://github.com/samertts/gula-platform)
**نطاق التقرير:** التبعيات المحلولة فعلياً في Python وNode.js/pnpm وAndroid/Maven، مع مراجعة خاصة لمسارات التبعيات العابرة والتنبيهات السابقة من Dependabot.

## الخلاصة التنفيذية

اكتمل الفحص الأمني الإضافي للتبعيات القابلة للتشغيل في المستودع. لم تُكتشف **أي ثغرة مؤكدة في النسخ المحلولة فعلياً** ضمن نتائج `pip-audit` و`npm audit` و`pnpm audit` وفحص OSV لتبعيات Maven/Android. شمل فحص OSV **531 حزمة Maven محلولة** من configurations الخاصة بتطبيق Android، وكانت النتيجة صفر findings.

> **النتيجة:** حالة التبعيات المحلية المفحوصة هي «صفر ثغرات مؤكدة». ولا تعني هذه النتيجة إغلاق تنبيه GitHub Dependabot #471 تلقائياً؛ فحالة التنبيه على GitHub يجب أن تُراجع بشكل مستقل بعد اكتمال إعادة الفحص في GitHub.

## جدول النتائج

| النطاق | الأداة أو المنهج | النتيجة المثبتة | ملاحظة التحقق |
|---|---|---:|---|
| Python | `pip-audit` على lockfiles وملفات requirements المتتبعة في backend وedge_agent وhospital_desktop وnhop-platform وplatform والجذر | **صفر ثغرات** | لم تُرجع الفحوص ثغرات معروفة في النسخ المثبتة؛ المرجع المنهجي هو [pip-audit][2]. |
| Node.js/Expo | `npm audit` على المشاريع ذات lockfiles npm، و`pnpm@10.4.1 audit` على مشاريع pnpm المقفلة | **صفر ثغرات** | جميع counters المتاحة: info/low/moderate/high/critical = صفر في المشاريع التي شملها الفحص. |
| ui-refresh | تثبيت `pnpm install --frozen-lockfile` ثم `pnpm audit` بعد تحديث wouter وفرض esbuild | **install ناجح، audit صفر** | `esbuild` محلول إلى `0.25.12`، و`wouter` محلول إلى `3.10.0` مع patch المقصود؛ أداة `drizzle-kit` تعمل بإصدار `0.31.10`. |
| radiology | مراجعة الاستخدام ثم إزالة Cornerstone غير المستخدمة من manifest وإعادة الفحص | **صفر ثغرات** | أزيلت `@cornerstonejs/core` و`@cornerstonejs/tools` و`@cornerstonejs/adapters` بعد التحقق من عدم استخدامها في المسار المفحوص، لتقليل سطح الهجوم وسلسلة التبعيات. |
| Android/Maven | استخراج النسخ من تقارير Gradle الفعلية، ثم `OSV querybatch` على النسخ المحلولة | **531 حزمة، صفر findings** | شملت configurations: `debugRuntimeClasspath` و`releaseRuntimeClasspath` و`debugAndroidTestRuntimeClasspath` و`debugAndroidTestCompileClasspath`، إضافة إلى التقارير العامة القابلة للتشغيل. |
| Android pins | `resolutionStrategy` وdependency insight وتقارير Gradle | **Netty 4.1.137.Final** | الظهورات المحلولة لـ Netty في configurations المفحوصة هي النسخة المثبتة؛ وظهر كذلك OkHttp محلولاً إلى `4.12.0`. |
| drizzle-kit | تشغيل binary المحلي `./node_modules/.bin/drizzle-kit --version` | **ناجح** | `drizzle-kit: v0.31.10` و`drizzle-orm: v0.45.2`. |

## معالجة النتائج الخاصة بـ ui-refresh

ظهر في الفحص الأول مسار عابر متأثر مرتبطاً بـ `esbuild`، ولذلك أضيف override صريح إلى `0.25.12`، مع تحديث `wouter` إلى `3.10.0` ونقل patch instrumentation إلى `patches/wouter@3.10.0.patch`. أُعيد توليد `pnpm-lock.yaml`، ثم تحقق التثبيت باستخدام `--frozen-lockfile`، وأعيد تشغيل التدقيق بعد التثبيت. لا يُعد نجاح التثبيت بديلاً عن التدقيق؛ النتيجة المقبولة هنا هي اجتماع نجاح التثبيت المقفول مع نتيجة audit الخالية من findings.

يجب أن يبقى override موثقاً ومراجَعاً عند تحديث pnpm أو esbuild، لأن إعدادات `overrides` و`patchedDependencies` تؤثر في resolver وسلسلة التبعيات العابرة كما هو موضح في [إعدادات pnpm 10][4].

## معالجة نتائج Android/Maven

أظهر الفحص الأول على النسخ المطلوبة أو الظاهرة في بعض ملفات البناء عدداً من GHSA hits. أُعيدت عملية الاستخراج من **تقارير Gradle التي تحتوي على النسخة المحلولة النهائية**، بدلاً من الاعتماد على النسخة المطلوبة قبل تطبيق `resolutionStrategy`. بعد ذلك أرسل الفحص 531 حزمة Maven إلى OSV عبر query batch؛ النتيجة المحفوظة هي:

```json
{
  "findings": [],
  "scanned": 531
}
```

بذلك تُصنف hits الأولية كإيجابيات كاذبة بالنسبة إلى graph المحلول الحالي، لا كإثبات لوجود ثغرة في artifact المستخدم فعلياً. هذا الاستنتاج محدود بما تم حله وبما أُدرج في configurations المفحوصة؛ ويجب إعادة الفحص بعد كل تغيير في Gradle أو Android/UTP. تدعم وثائق Gradle استخدام قواعد resolution لتثبيت أو استبدال نسخ التبعيات في graph المحلول [5]، بينما يوفر OSV واجهة batch لمطابقة الحزم والإصدارات مع advisories المعروفة [1].

## حالة Dependabot وقرار الإغلاق

لا يجوز مساواة الفحص المحلي بإغلاق تنبيه GitHub. أثناء التدقيق كان التنبيه [Dependabot #471][6] المتعلق بـ Netty ظاهراً كمفتوح بدرجة Moderate، رغم أن graph المحلي حل Netty إلى `4.1.137.Final`، وهي النسخة التي استُخدمت في التحقق المحلي. لذلك تبقى حالة GitHub منفصلة إلى أن يكتمل تحليل dependency file في GitHub وتُراجع صفحة التنبيه أو API بصلاحيات كافية.

| البند | الحالة | القرار |
|---|---|---|
| ثغرات مؤكدة في النسخ المحلولة محلياً | **0** | لا توجد معالجة إضافية مطلوبة من نتائج الفحص الحالي. |
| Netty في graph Android المحلي | **مثبت إلى 4.1.137.Final** | أعيد التحقق عبر Gradle configurations وdependency graph. |
| Dependabot #471 على GitHub | **يحتاج إعادة تحقق مستقل** | لا يُغلق يدوياً ولا يُعلن أنه false positive قبل تحديث GitHub. |
| إطلاق بيانات صحية حقيقية | **غير موصى به بعد** | يتطلب إغلاق/تفسير التنبيه، مراجعة سريرية، واختبارات اختراق وامتثال مستقلة. |

## الملفات والتغييرات المرتبطة بالتدقيق

| الملف | التغيير |
|---|---|
| `apps/gula-platform-ui-refresh/package.json` | تحديث `wouter` إلى `3.10.0` وإضافة override لـ `esbuild: 0.25.12`. |
| `apps/gula-platform-ui-refresh/patches/wouter@3.10.0.patch` | patch محدث للحفاظ على instrumentation المسارات. |
| `apps/gula-platform-ui-refresh/pnpm-lock.yaml` | lockfile مولد بعد التحديث، مع graph محلول قابل لإعادة الإنتاج. |
| `platform/apps/radiology/package.json` | إزالة حزم Cornerstone غير المستخدمة. |
| `mobile/android/settings.gradle.kts` وملفات Gradle ذات الصلة | pins وresolution rules الخاصة بـ Netty وBouncy Castle كما سُجلت في commits السابقة. |
| `docs/DEPENDABOT_GITHUB_STATUS_2026-08-20.md` | سجل زمني لحالة Dependabot، من دون ادعاء إغلاق التنبيه. |

## القيود والخطوات المتبقية

هذا التدقيق يثبت حالة التبعيات في لحظة الفحص ولا يحل محل المراقبة المستمرة. ينبغي تشغيل `pip-audit` و`npm/pnpm audit` وOSV أو خدمة مكافئة في CI على كل تغيير lockfile، مع منع البناء عند وجود ثغرة عالية أو حرجة غير مبررة. كما ينبغي حفظ تقارير scan كـ CI artifacts، وتسجيل نسخة الأداة وتاريخ الفحص والـ commit المستهدف.

قبل الإطلاق ببيانات صحية حقيقية، يجب إعادة فتح [صفحة Dependabot][6] بعد اكتمال إعادة الفحص، ثم تنفيذ مراجعة أمنية مستقلة، واختبار اختراق، وتمرين استعادة، ومراجعة سياسات الاحتفاظ والحذف والتشفير والتدقيق بما يتوافق مع HIPAA وGDPR وPDPL. تبقى مسارات Clinical AI غير المنفذة على HTTP 501، والمسارات غير المهيأة على HTTP 503، ولا يجوز استخدام نتيجة هذا التدقيق لتفعيل قرارات علاجية آلية أو مزودات Wearables حية.

## المراجع

[1]: https://osv.dev/docs/#tag/querybatch "OSV Query Batch API"
[2]: https://github.com/pypa/pip-audit "pip-audit — Python dependency vulnerability scanner"
[3]: https://docs.npmjs.com/cli/v10/commands/npm-audit "npm audit documentation"
[4]: https://pnpm.io/10.x/settings "pnpm 10 settings: overrides and patched dependencies"
[5]: https://docs.gradle.org/current/userguide/resolution_rules.html "Gradle dependency resolution rules"
[6]: https://github.com/samertts/gula-platform/security/dependabot/471 "GULA GitHub Dependabot alert #471"
