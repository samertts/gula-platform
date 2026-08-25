# سجل الأدلة المحلية لمرشح الإصدار RC1

**المرشح المفحوص:** `release/clinical-safety-2026q3-rc1`
**SHA المفحوص:** `dfd9396275393c95e596a9b8a2416dc00956b1a6`
**وقت التنفيذ:** 25 أغسطس 2026 (GMT+3)
**الحالة:** **NO-GO** — هذا السجل يوثق نتائج محلية ولا يحل محل CI أو UAT أو توقيعات بشرية أو قرار إطلاق.

> لا يوجد في هذا السجل PHI أو أسرار أو keystore أو معلومات دفع. لا يجوز نقل أي قيمة من هذا الملف إلى manifest الرسمي على أنها PASS نهائي إلا بعد التحقق من أن الدليل نُفذ على SHA النهائي نفسه وبواسطة المالك المخول حيث يقتضي الأمر ذلك.

## 1. الأدلة المنفذة

| المجال | الأمر/النطاق | النتيجة | التفسير |
|---|---|---|---|
| تثبيت المرشح | إنشاء `release/clinical-safety-2026q3-rc1` | **تم** | الفرع مثبت عند SHA المذكور أعلاه؛ لم يدمج إلى `main` أو `develop`. |
| انحدار الخلفية | `cd backend && pytest -q` | **2742 ناجح، 4 متخطى، 0 فشل** | دليل محلي قوي ومعاصر للمرشح؛ ظهرت تحذيرات deprecation غير مانعة، ولا تغني عن CI. |
| بوابة الجودة التفاضلية | مقارنة merge-base الفعلي مع RC1 | **PASS** | انخفض Ruff للملفات المتغيرة من 123 إلى 68 وMypy من 79 إلى 78؛ نطاقات MyPy الحرجة بقيت 510 بلا زيادة. |
| بوابة الجودة الموحدة | `scripts/quality_gate.py` | **FAIL** | architecture وdebt فاشلان؛ لا يجوز تسجيل جودة شاملة PASS أو تجاهل ذلك. |
| سياسة الترحيلات | `scripts/check_migration_policy.sh` | **PASS** | لا مخالفة سياسة ظاهرة في الفحص المحلي. |
| رأس Alembic | `alembic heads` | **`20260825_0008` head واحد** | يحتاج ترقية staging وbackup/restore قبل PASS رسمي للترحيلات. |
| تدقيق Python | `pip-audit -r backend/requirements.txt` | **لا CVE معروفة** | فحص اعتمادات فقط؛ لا يحل محل مراجعة الأمن أو CodeQL في CI. |
| تدقيق Expo | `npm audit --omit=dev --audit-level=moderate --package-lock-only` | **0 vulnerabilities** | الاعتمادات الإنتاجية في Expo لا تظهر ثغرات معروفة في هذا الفحص. |
| فحوص Expo | typecheck + Jest + اختبار parser الأمني | **PASS: 4/4** | `tsc --noEmit` ناجح واختبار `image-size` الأمني ناجح. |
| Gradle Android | `./gradlew help` | **PASS** | التهيئة قابلة للتحميل من دون مفاتيح توقيع. |
| ضابط توقيع Android | `./gradlew bundleRelease` بلا secrets | **PASS سلبي** | رفض صحيح: لا يسمح ببناء release غير موقّع. لا يوجد AAB موقّع بعد. |

## 2. العوائق التي تبقي القرار NO-GO

| العائق | الوضع | المالك | الإجراء التالي الذي لا يمكن استبداله |
|---|---|---|---|
| CI الرسمي | لم يبدأ سابقاً بسبب عائق حساب/إنفاق GitHub | مالك حساب GitHub | معالجة حالة الحساب ثم تشغيل pipeline كاملاً على SHA المرشح. |
| الجودة الموحدة | فشل architecture وdebt | الهندسة/الأمن | تحليل التفاصيل، فصل الإصلاح إلى دفعات، وإعادة فحص البوابة؛ لا استثناء صامت. |
| ترحيلات staging | لم ينفذ upgrade وrestore حقيقيان | مالك قاعدة البيانات | ترقية staging، اختبار backup/restore، وتسجيل الدليل. |
| AAB موقّع | غير متاح | مالك إصدار Android | بناء عبر أسرار CI المعتمدة، فحص التوقيع، واختبار جهاز فعلي. |
| UAT | لم ينفذ | قائد UAT السريري | تنفيذ سجل UAT التركيبي على SHA نفسه، وتسجيل النتائج. |
| التوقيعات | غير متاحة | الأدوار المخولة | توقيعات LIMS والسريرية والأمن والمنصة والسلامة بأسماء وتواريخ حقيقية. |
| manifest الرسمي | حقول مرشح/أدلة وحالات PASS ما زالت `PENDING` | مدير الإصدار | تعبئته بعد إغلاق الأدلة فقط، ثم تشغيل الفاحص. |
| الجهاز الحي | غير مؤهل | مدير الإصدار/السلامة | يبقى معطلاً؛ لا يدخل ضمن GO المرحلة الأولى. |

## 3. التسليم إلى الملاك

تستخدم هذه الملفات معاً، ولا تمثل أي منها توقيعاً أو تفويضاً:

1. [`GO_LAUNCH_OWNER_ACTIONS_AR.md`](GO_LAUNCH_OWNER_ACTIONS_AR.md): تسلسل الملاك وحظر تجاوز CI أو التوقيعات.
2. [`RC1_SYNTHETIC_UAT_EXECUTION_RECORD_AR.md`](RC1_SYNTHETIC_UAT_EXECUTION_RECORD_AR.md): سجل UAT التركيبي الذي يعبئه فريق مؤهل في staging.
3. [`GO_LAUNCH_EVIDENCE_MANIFEST.json`](GO_LAUNCH_EVIDENCE_MANIFEST.json): السجل الرسمي الذي يبقى PENDING/NO-GO إلى حين إثبات كل بند.
4. [`DEVICE_MEASUREMENT_HUMAN_ACCEPTANCE_DESIGN_AR.md`](DEVICE_MEASUREMENT_HUMAN_ACCEPTANCE_DESIGN_AR.md): يثبت أن قبول القياسات أو إنشاء النتائج من جهاز ليسا جزءاً من هذا الإطلاق.

## 4. شرط الانتقال التالي

بعد أن يعالج مالك GitHub العائق وتشغل CI على SHA المرشح، يجمع مدير الإصدار روابط CI والأدلة المؤرخة. بعد UAT والتوقيعات وترحيلات staging وAAB الموقع، يشغّل الفاحص:

```bash
python3 scripts/release_go_preflight.py --json
```

المخرج المقبول قبل اجتماع القرار هو `HUMAN_GO_DECISION_REQUIRED`. أما `NO_GO` فهو حظر صريح؛ يعالج البند المسجل ولا يرفع الإصدار.

## المراجع

[1] [سجل بوابة السلامة السريرية وUAT](RELEASE_CLINICAL_SAFETY_UAT_GATE_STATUS_AR.md)
[2] [حزمة إجراءات الملاك قبل GO](GO_LAUNCH_OWNER_ACTIONS_AR.md)
[3] [سجل تنفيذ UAT التركيبي RC1](RC1_SYNTHETIC_UAT_EXECUTION_RECORD_AR.md)
[4] [manifest أدلة GO](GO_LAUNCH_EVIDENCE_MANIFEST.json)
