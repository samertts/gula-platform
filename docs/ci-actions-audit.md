# تدقيق إخفاقات GitHub Actions — GULA Platform

**الحالة:** اكتمل إصلاح الأسباب القابلة لإعادة الإنتاج محليًا؛ تبقى متطلبات بنية تحتية وأسرار موثقة أدناه.
**تاريخ الحصر:** 12 أغسطس 2026
**المصدر:** GitHub Actions repository run API and failed-job logs

## الحصر الأولي

استُرجع **1,000 تشغيل فاشل متاح عبر واجهة GitHub Actions**. هذا الرقم يمثل السجل المتاح من الواجهة في وقت التدقيق وقد يتضمن تكرارات تاريخية لنفس السبب؛ لذلك يجري قياس الأسباب الفريدة وإصلاح ملفات سير العمل الحالية بدل معالجة كل تشغيل قديم منفردًا.

| سير العمل/الاسم التاريخي | إخفاقات في السجل المسترجع | سبب ممثل تم جمعه |
| --- | ---: | --- |
| CI Pipeline وCI - Build, Test & Security Scan | 475 | فشل flake8 في السجل الأحدث؛ إخفاقات بناء/Trivy تاريخية مع tags فروع غير صالحة |
| Deploy GULA Platform / Verify Railway Deployment | 136 | مصادقة SSH فاشلة (`Permission denied`) |
| CodeQL Advanced | 63 | لغات بلا مصدر أو autobuild غير قابل للتحديد (Ruby/Swift/Java) |
| Constitution Compliance | 63 | سجل ممثل من ملف/سير عمل تاريخي لم تعد سجلاته متاحة |
| Quality Gate / Production Quality Gates | 64 | YAML غير صالح؛ مراجع submodule غير معرفة؛ متطلبات PWA غير واقعية في سجل أقدم |
| Frontend PWA وE2E | 59 | مسار artifact `frontend-v2/build` مفقود وweb server لم يبدأ خلال المهلة |
| Mobile Android/iOS/Flutter Desktop | 24 | إعداد Gradle/اعتماد Flutter غير صالح؛ workspace iOS مفقود |
| SDK Publish Packages | 5 | إصدار Flutter action غير متاح؛ نشر حزم يحتاج معالجة release/credentials |
| Dependency Review | 20 | قائمة تراخيص غير صالحة في إعداد الإجراء |
| OpenSSF Scorecard | 16 | checkout يتعامل مع مجلد مضمّن كـsubmodule بلا URL |

## الأدلة التقنية المختصرة

1. أحدث CI Pipeline فشل في مرحلة `Syntax Gate / Lint with flake8` فقط؛ بقية مراحل الاختبار والترحيل لم تبدأ بسبب الاعتماد على هذه البوابة.
2. سجل CodeQL يثبت أن Ruby غير موجودة ضمن مصدر المشروع وأن Java/Kotlin وSwift لا يملكان أمر بناء تلقائي قابلًا للاكتشاف. يجب ضبط اللغات والبناء يدويًا بدل الفشل التلقائي.
3. سجل iOS يثبت غياب `Gula.xcworkspace`، وليس فشل اختبار iOS حقيقيًا؛ يجب اكتشاف المشروع/الـworkspace ثم تخطي المسارات غير الموجودة بصورة صريحة أو تثبيت مسار المشروع الصحيح.
4. سجل Flutter Desktop وSDK يثبت أن `subosito/flutter-action@v3` غير قابل للحل، لذا يجب تثبيت إصدار صالح ومثبت أو إيقاف job المشروط عند غياب مشروع Flutter.
5. سجل النشر يتطلب إصلاح سر/مفتاح SSH أو تحويل النشر إلى مزود موثق؛ لا يمكن اختراع بيانات اعتماد من داخل المستودع.

## مراجع التشغيل

- [أحدث CI Pipeline فاشل](https://github.com/samertts/gula-platform/actions/runs/31641735327)
- [أحدث CodeQL Advanced فاشل](https://github.com/samertts/gula-platform/actions/runs/31601169224)
- [أحدث Verify Railway Deployment فاشل](https://github.com/samertts/gula-platform/actions/runs/31601169117)
- [أحدث Mobile iOS CI/CD فاشل](https://github.com/samertts/gula-platform/actions/runs/31603286513)
- [أحدث SDK Publish Packages فاشل](https://github.com/samertts/gula-platform/actions/runs/31602450263)

> لا تُعامل أخطاء الأسرار أو شهادات النشر بوصفها أخطاء كود: سيُعالج منطق سير العمل وشرطه، لكن ستبقى البيانات الحساسة مطلوبة من مالك بيئة النشر عند الحاجة.

## مراجع الإصلاحات

تؤكد وثائق Android Developers أن `androidx.biometric:biometric:1.1.0` هو الإصدار المستقر المنشور، وأن `androidx.security:security-crypto:1.1.0` هو الإصدار المستقر المنشور. استُبدلت الإصدارات غير القابلة للحل في Gradle بهذين الإصدارين. تعذّر تشغيل بناء Android محليًا فقط لغياب Android SDK في بيئة الفحص؛ سير عمل Android يهيّئ SDK قبل البناء، ولذلك يجب أن يتحقق منه التنفيذ البعيد.

- [AndroidX Biometric releases](https://developer.android.com/jetpack/androidx/releases/biometric)
- [AndroidX Security releases](https://developer.android.com/jetpack/androidx/releases/security)

## الإصلاحات التي أُجريت

| المجال | الإصلاح | الحالة |
| --- | --- | --- |
| Python CI | أزيل الاستيراد المكرر في مصنع التطبيق، ورُفعت `pytest-asyncio` إلى سلسلة متوافقة مع pytest 9، وأضيفت `pytest-timeout` لاعتماد أوامر CI والمهام الليلية. | متحقق محليًا |
| PWA | صُححت مخرجات Vite من `build/` إلى `dist/`، وأضيف إعداد Lighthouse، وقُيد نشر Vercel بالتشغيل اليدوي. | متحقق محليًا |
| E2E | وُحِّد استرجاع جلسة HttpOnly المحاكية، وحُجبت Service Workers في الاختبارات، وصُححت اعتراضات API وعقود بيانات المرضى والنتائج والعينات. | متحقق محليًا |
| Flutter وSDK | استُخدم إصدار Flutter action صالح، وحُصر نشر SDK في الإصدار المنشور أو التشغيل اليدوي المصرح. | قيد التحقق البعيد |
| Android | ثُبتت إصدارات AndroidX القابلة للحل. | قيد التحقق البعيد لغياب SDK محليًا |

## نتائج التحقق المحلي

| الفحص | النتيجة |
| --- | --- |
| اختبارات الخلفية الكاملة: `pytest tests/ -v --timeout=60 -x` | **2,337 ناجحًا** و**6 حالات فرعية ناجحة** |
| بوابة CI لـ flake8: `flake8 app/ --select=E9,F --ignore=F401,F841 --count` | **0 مخالفات** |
| اختبارات Playwright E2E الكاملة | **40 ناجحًا** |
| lint وTypeScript واختبارات الوحدة في `frontend-v3` | **ناجحة**؛ لا توجد اختبارات وحدة مكتشفة بعد الاستبعاد المقرر لـ E2E |
| بناء الإنتاج لـ `frontend-v2` و`frontend-v3` | **ناجح**، مع توليد Service Worker في كل منهما |

## متطلبات خارج نطاق تعديل الشفرة

| سير العمل | المتطلب | الإجراء المطلوب من مالك بيئة النشر |
| --- | --- | --- |
| Deploy GULA Platform | مفتاح أو سر SSH صالح | إضافة/تدوير السر المطلوب في أسرار GitHub ثم إعادة تشغيل النشر. |
| Mobile iOS CI/CD | مشروع أو workspace Xcode فعلي | تثبيت مسار المشروع الصحيح أو إضافة `Gula.xcworkspace` إلى المستودع. |
| Android المحلي | Android SDK | لا يلزم تعديل للمستودع؛ تتولى بيئة CI إعداد SDK، لكن ينبغي مراقبة التشغيل البعيد التالي. |

> لم تُنفذ أي عملية نشر للإنتاج أو نشر حزمة إلى سجل خارجي ضمن هذا العمل؛ قيود سير العمل تمنع النشر غير المقصود، وتبقى الأسرار والإصدارات الرسمية تحت سيطرة المالك.
