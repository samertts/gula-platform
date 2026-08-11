# حالة تطبيقات الهاتف وDesktop/EXE

تمت مواءمة عقود المصادقة في التطبيق المكتبي مع الخلفية الحالية. يقرأ Desktop الآن `access_token` القياسي أو `token` القديم، يدعم استجابة `user` المتداخلة، يتحقق من `/session` بدل `/auth/me` غير الموجود، ويملك مسار `startDemo()` لزر العرض المعزول. تظل الرموز في Desktop داخل `flutter_secure_storage`، ولا تُكتب في ملفات السجل أو عناوين URL.

تستخدم Android وiOS أصلًا Keychain/EncryptedPrefs وحقول `access_token` و`refresh_token`، وقد دعمت الخلفية هذه الحقول في login وrefresh مع تدوير refresh token. يجب تشغيل التطبيقين على عنوان API الخاص بالبيئة نفسها؛ لا يجوز أن يشير build تجريبي إلى API الإنتاج.

## متطلبات البناء

لبناء Desktop/EXE يجب توفر Flutter SDK، ثم:

```bash
cd mobile/desktop
flutter pub get
flutter analyze
flutter test
flutter build windows --release
```

لبناء Android:

```bash
cd mobile/android
./gradlew test
./gradlew assembleRelease
```

ولـ iOS يلزم macOS وXcode وCocoaPods. بيئة الفحص الحالية لا تحتوي Flutter، وGradle wrapper في Android يفتقد `GradleWrapperMain`، ولا تحتوي Xcode أو MSBuild؛ لذلك لم يُعلن نجاح حزم native من دون تشغيلها في بيئة البناء المناسبة.

## شرط التحقق قبل الإصدار

قبل رفع أي APK/IPA/EXE، يجب اختبار login، MFA، refresh rotation، logout، session restoration، رفض الحساب غير الموثق، زر العرض التجريبي، وفصل قاعدة البيانات التجريبية. كما يجب فحص أن كل endpoint حساس يعيد 401/403 عند غياب الجلسة وأن التخزين المحلي لا يحتوي إلا على بيانات الاعتماد المشفرة الخاصة بالمنصة الأصلية.
