# سياسة تحديث تطبيقات GULA

هذه الوثيقة تصف آلية تجهيز التحديثات لجميع تطبيقات GULA، بما فيها iOS. لا تنفذ الآلية نشرًا تلقائيًا أو تثبيتًا صامتًا؛ بل تفحص بيان إصدار عام، وتعرض رابط الإصدار أو المتجر، وتمنع الدخول فقط عندما يعلن الخادم صراحة أن الإصدار الحالي أقل من الحد الأدنى المدعوم.

## التطبيقات المشمولة

| المنصة | الإصدار الموحّد | معرّف/وجهة الإصدار |
|---|---:|---|
| Web/PWA | 2.5.0 | نطاق GULA الإنتاجي |
| Android | 2.5.0 / versionCode 20500 | `io.gula.android` وGoogle Play عند تفعيل النشر |
| Windows | 2.5.0 / MSIX 2.5.0.0 | `com.gulaplatform.desktop` وMSIX/إصدار Desktop |
| macOS | 2.5.0 | DMG/قناة Desktop |
| iOS | 2.5.0 | Bundle ID وتطبيق App Store عند تفعيل النشر |
| Linux | 2.5.0 | AppImage وdeb وrpm |

## سلوك التحديث

يُطلب `GET /app-updates?platform=<platform>&version=<version>` دون مصادقة، وتقبل قيمة `platform` الآن: `web` و`android` و`ios` و`windows` و`macos` و`linux`. يعيد المسار metadata فقط، ومنها `latest_version` و`minimum_supported_version` و`update_available` و`force_update` و`store_url`. لا يحتوي الرد على بيانات مرضى أو مفاتيح أو إعدادات بنية داخلية.

عندما يكون `update_available=true` يستطيع المستخدم تأجيل التحديث في Web/Desktop/Android/iOS. عندما يكون `force_update=true` أو يكون الإصدار الحالي أقل من `minimum_supported_version`، يعرض التطبيق شاشة تمنع متابعة الاستخدام السريري حتى يفتح رابط التحديث. إذا تعذر الوصول إلى manifest مؤقتًا، يعمل التطبيق في وضع fail-open ولا يمنع الوصول، حتى لا يتحول عطل خدمة metadata إلى انقطاع سريري.

## تفعيل تحديث إجباري لاحقًا

يُرفع الحد الأدنى للإصدار في بيئة الإنتاج عبر متغيرات Railway المقابلة للمنصة، مثل `GULA_ANDROID_MINIMUM_SUPPORTED_VERSION=2.6.0`، بعد التأكد من أن الإصدار 2.6.0 منشور ومتاح للمستخدمين. يجب تعيين `GULA_ANDROID_LATEST_VERSION=2.6.0` في الوقت نفسه، ثم التحقق من endpoint قبل إعلان الإلزام.

ينبغي عدم جعل minimum version أعلى من latest version؛ endpoint يقوم بتصحيح هذا الترتيب إلى latest لأسباب fail-safe. بعد تفعيل الإلزام يجب اختبار نسخة قديمة تركيبية ونسخة حديثة لكل منصة، بما فيها iOS، والتأكد من أن القديمة لا تصل إلى شاشات clinical وأن الحديثة لا تظهر لها شاشة إجبارية. في iOS يفتح رابط `GULA_IOS_STORE_URL` عبر `UIApplication`/SwiftUI `openURL`؛ لا يحاول التطبيق تثبيت IPA خارج App Store.

## ضوابط الإصدار

يجب زيادة Android `versionCode` في كل إصدار Google Play، وعدم إعادة استخدام رقم سبق رفعه. في iOS يجب زيادة `CFBundleShortVersionString` و`CFBundleVersion`، وربط رابط App Store بمعرّف التطبيق الصحيح قبل تفعيل الإلزام. أما Desktop فيجب تحديث pubspec وMSIX version معًا. يجب حفظ مفاتيح التوقيع في GitHub/Railway secret manager فقط، وعدم تضمينها في artifacts أو commits أو logs. لا يُنفذ النشر من هذه التغييرات؛ workflows تظل مسؤولة عن البناء والتحقق، ويحتاج رفع المتاجر إلى حسابات وموافقات المزود المناسبة.
