# نتائج Dependabot الخارجية — 2026-08-19

## مصدر قائمة التنبيهات

تمت قراءة صفحة GitHub Security الخاصة بالمستودع `samertts/gula-platform` عبر الجلسة الموثقة:

- https://github.com/samertts/gula-platform/security/dependabot

أظهرت الصفحة 8 تنبيهات مفتوحة على commit الفحص `8946d21`، موزعة على 4 عالية و4 متوسطة، وجميع تنبيهات npm في `mobile-expo/package-lock.json` باستثناء Netty في Android.

| رقم التنبيه | الحزمة | Ecosystem | Manifest | الشدة | الموضوع |
|---:|---|---|---|---|---|
| 478 | image-size | npm | mobile-expo/package-lock.json | High | ICNS parser infinite loop |
| 477 | image-size | npm | mobile-expo/package-lock.json | High | JXL/HEIF parser infinite loops |
| 474 | postcss | npm | mobile-expo/package-lock.json | High | arbitrary file read via attacker-controlled sourceMappingURL |
| 475 | postcss | npm | mobile-expo/package-lock.json | High | path traversal in previous source map auto-loading |
| 473 | uuid | npm | mobile-expo/package-lock.json | Moderate | missing buffer bounds check in v3/v5/v6 |
| 476 | postcss | npm | mobile-expo/package-lock.json | Moderate | incomplete sourceMappingURL fix when `from` is unset |
| 471 | io.netty:netty-codec-http | Maven | mobile/android/settings.gradle.kts | Moderate | CORS Vary header cache poisoning/information disclosure |
| 472 | postcss | npm | mobile-expo/package-lock.json | Moderate | XSS via unescaped `</style>` in CSS stringify output |

## GitHub Advisory Database

### image-size

- ICNS: https://github.com/advisories/GHSA-w3rx-r6r6-pgpr
- JXL/HEIF: https://github.com/advisories/GHSA-5p2g-fcmc-qvqq
- CVE-2025-71330 وCVE-2025-71329.
- النطاق المتأثر: `image-size <= 2.0.2`.
- GitHub يذكر صراحة: **Patched versions: None**.
- السبب التقني: حقول box/entry ذات قيمة صفرية لا تزيد offset داخل parser، ما قد يوقف event loop بحلقة لا نهائية.
- مصدر upstream الذي يتضمن جزءاً من الإصلاح: https://github.com/image-size/image-size/commit/8994131c7c3ee8da1699e04700c95e0e683a0c68 (إصلاح `findBox` في 2025، لكنه ليس إصدار npm مصححاً ولا يعالج ICNS مباشرة).

### PostCSS

- https://github.com/advisories/GHSA-fxqj-rqcc-2cmp
- النطاق المتأثر: `postcss <= 8.5.22`.
- الإصدار المصحح: `8.5.23`.
- الإصدار المتاح وقت الفحص: `8.5.26`.
- الثغرة تتعلق بقراءة `.map` مطلقة أو عبر traversal عندما لا يكون `from` مضبوطاً.

### uuid

- https://github.com/advisories/GHSA-w5hq-g745-h8pq
- النطاق المتأثر: `<11.1.1`، وكذلك نطاقات `<12.0.1` و`<13.0.1` حسب major.
- الإصدار المصحح المتوافق مع major 11: `11.1.1`.
- الإصلاح يتحقق من أن `offset + 16` داخل buffer في v3/v5/v6.

## نتائج npm audit المحلية

تم تشغيل `npm audit --json` على `mobile-expo`، وظهر أن `image-size` و`postcss` و`uuid` عابرة، وأن npm يقترح ترقية `expo` إلى `57.0.14` كحل شامل major upgrade. لا يجوز تنفيذ هذه الترقية العمياء دون تحديث Expo/React Native واختبارات mobile كاملة.

## قرار المعالجة

PostCSS وuuid قابلان للترقية القسرية/الموجهة إلى الإصدارات المصححة مع اختبار Expo/Metro. أما image-size فلا يوجد له إصدار npm مصحح بحسب GitHub Advisory، ولذلك لا يُغلق التنبيه بمجرد override إلى إصدار أقدم أو أحدث غير مصحح. يلزم إما تحديث Expo/Metro إلى سلسلة تزيل image-size، أو استخدام patch/repository مبني ومراجع يطبق حواجز parser مع توثيق ذلك واختبار payloads ذات أحجام صفرية قبل اعتبار التنبيه مغلقاً.

## نتيجة الإصلاح في هذه المراجعة

تم إنشاء fork محلي minimal من `image-size@2.0.2` داخل `mobile-expo/vendor/image-size` بإصدار داخلي `2.0.3`. أضيفت حواجز إلى نسختي ESM وCommonJS المنفصلتين وإلى bundles `dist/index.*` التي يستوردها Metro: رفض `ICNS` entry عندما يكون الحجم أصغر من header أو يتجاوز buffer، ورفض HEIF/JXL box عندما يكون حجمه أصغر من 8 bytes أو يتجاوز buffer. أضيف اختبار `mobile-expo/scripts/test-image-size-security.mjs` يغطي ESM وCommonJS وICNS وHEIF وJXL، وقد نجح.

تم تثبيت `postcss@8.5.26` و`uuid@11.1.1` عبر `overrides`، وربط `image-size` المحلي كاعتماد مباشر مع override مرجعي حتى يعاد استخدامه داخل Metro. أزيلت devDependencies من manifest المحلي حتى لا تدخل `glob` و`tsup` و`esbuild` غير اللازمة إلى شجرة mobile runtime.

تمت إعادة تشغيل `npm install --package-lock-only --ignore-scripts --no-audit` ثم `npm audit --json` على `mobile-expo`: النتيجة النهائية `0` ثغرات معلوماتية أو منخفضة أو متوسطة أو عالية أو حرجة. كما نجح `npm run test:security`.

بالنسبة إلى Netty، يثبت advisory الرسمي [GHSA-8c42-7qj2-3j46](https://github.com/netty/netty/security/advisories/GHSA-8c42-7qj2-3j46) أن `4.1.137.Final` هو الإصدار المصحح لسلسلة 4.1، وقد ثُبت هذا الإصدار في جميع configurations ذات الصلة داخل `mobile/android/build.gradle.kts`. المصدر البديل [OSV CVE-2026-59903](https://osv.dev/vulnerability/CVE-2026-59903) يؤكد الإصلاح في `4.1.137.Final` و`4.2.17.Final`.

> ملاحظة تشغيلية: ستظل صفحة GitHub تعرض التنبيهات حتى تفحص Dependabot commit جديداً بعد الدفع؛ لا يجوز اعتبار الحالة المرئية محدثة قبل اكتمال إعادة الفحص من GitHub.

## تحقق CI المحلي

نجحت الخطوات المطابقة لـ `mobile-expo.yml`: اختبارات الوحدة (`4/4`)، `typecheck`، اختبار parser الأمني، فحص Expo config safety invariants، `npm audit` الكامل بنتيجة صفر، و`expo-doctor` بنتيجة `17/17`. كما أزيل fallback الصامت من خطوة audit في workflow وأضيف `test:security` كحاجز مستقل.
