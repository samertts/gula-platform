# GULA Mobile Speech-to-Text

هذا المجلد هو تطبيق Expo مستقل ومعزول لتطبيق أمر **GULA — Speech-to-Text Command 01** على Expo SDK 54. لم يتم تغيير Expo إلى SDK 55 أو 56 أو 57. تم تثبيت `expo-speech-recognition@3.0.0`، ومواءمة React Native إلى patch المتوافق مع SDK 54 وهو `0.81.5` فقط.

## المسار التشغيلي

المسار المطبق هو: **ضغط صريح على الميكروفون → طلب الصلاحية → Listening → Interim Text → Final Text → مراجعة بشرية → Append أو Replace بعد التأكيد → حفظ مسودة**. لا يتم تعديل سجل سريري أو تشخيص أو دواء مباشرة من نتيجة التعرف الصوتي، ولا يقوم المثال بإرسال البيانات إلى Backend؛ نقطة الربط الإنتاجية يجب أن تستدعي API GULA المصادق عليه بعد مراجعة المستخدم، وتتحقق من النسخة وتنتج سجل تدقيق غير قابل للتعديل.

## طبقة العزل

كل استدعاءات native موجودة داخل `src/speech/SpeechRecognitionService.ts`. الواجهة تستخدم `SpeechRecognitionProvider` و`useSpeechToText()` فقط، ولذلك يمكن تبديل المحرك أو إضافة موصل آخر دون ربط الشاشات بالمكتبة الأصلية. آلة الحالات تمنع الانتقالات غير المعرفة وتحوّل كل خطأ إلى حالة معروفة بدلاً من إسقاط التطبيق.

| المجال | التنفيذ |
|---|---|
| الحالات | `IDLE`, `REQUESTING_PERMISSION`, `READY`, `LISTENING`, `PROCESSING`, `FINALIZING`, `COMPLETED`, `DENIED`, `UNAVAILABLE`, `ERROR`, `CANCELLED` |
| اللغات المعتمدة | `ar`, `en-US`, `ku`, `tk`, `syr`؛ قد يظهر `ar-IQ` من الجهاز كمرادف محلي للعربية |
| تحقق اللغة | `getSupportedLocales()`؛ لا تُستخدم اللغة إلا بعد مطابقة ما يثبته محرك الجهاز |
| التعرف المحلي | يُطلب فقط عندما يثبت `supportsOnDeviceRecognition()`، ولا يدّعي التطبيق Offline عند غياب الإثبات |
| التسجيل | `continuous: false` و`recordingOptions.persist: false`؛ لا ملف صوتي محفوظ ولا تسجيل خلفي |
| الخصوصية | لا صوت في logs أو analytics، ولا transcript خارج الحقل الذي طلبه المستخدم؛ لا حفظ دائم أو إرسال شبكي في هذا المثال |
| دورة الحياة | إلغاء فوري عند الانتقال إلى background أو logout/session reset أو unmount |
| fallback | الإدخال اليدوي يبقى متاحاً عند رفض الصلاحية أو غياب المحرك أو اللغة أو الشبكة |
| المراجعة الطبية | النتيجة تبقى مسودة؛ لا تصحيح ذكي يغير المعنى الطبي تلقائياً |

## Android وiOS

يضيف `app.json` صلاحية `RECORD_AUDIO` على Android ورسائل واضحة للميكروفون والتعرف على الكلام على iOS. لا توجد صلاحية background audio ولا تشغيل تلقائي. لا تعتمد المنصة على Google Speech Service وحده؛ يتم فحص الخدمات المتاحة واللغات المثبتة، ويظهر fallback عندما تكون الخدمة غير متاحة. لا يعد Simulator دليلاً على الجهاز الحقيقي، لذلك يجب اختبار الميكروفون، Bluetooth/headset، المقاطعات، اللغات العربية، وانقطاع الشبكة على أجهزة فعلية.

## Expo Go وDevelopment Build

`expo-speech-recognition` هو native module، ولذلك لا ينبغي افتراض أن Expo Go يحتويه. استخدم Development Build بعد تثبيت الحزمة:

```bash
cd mobile-expo
npm ci
npx expo prebuild
npx expo run:android
# أو على macOS مع Xcode:
npx expo run:ios
```

لا تُضمّن مجلدات `android/` أو `ios/` المولدة في هذا التغيير ما لم يقرر فريق الإطلاق اعتماد CNG أو إدارة native يدوياً. ملف `app.json` هو مصدر إعداد الصلاحيات وconfig plugin في الوضع الحالي.

## الفحص والاختبارات

الأوامر المعتمدة هي:

```bash
npm run typecheck
npm test -- --runInBand
npx expo config --type public --json
npx expo-doctor --verbose
```

تغطي الاختبارات طلب الصلاحية، توفر اللغات، عدم حفظ التسجيل، interim/final، الانتقال إلى `COMPLETED`، وإلغاء الجلسة ومسح النص عند انتقال التطبيق إلى الخلفية. يتحقق CI من `expo config --type public --json` وثوابت العزل، ويفحص التبعيات وفق policy موثقة، ويشغّل Expo Doctor كـgate حاجز. الإصدار المحلي المثبت من Expo Doctor اجتاز `17/17` فحصاً دون مشاكل.

## عقد التكامل الإنتاجي

يستخدم المثال `sessionKey` محلياً لتمييز دورة العرض ولا يمثل مصادقة GULA. قبل ربط زر الحفظ بواجهة GULA الخلفية، يجب تمرير `sessionKey` ومُعرّف المستخدم من جلسة المصادقة، وإرسال **النص الذي راجعه المستخدم فقط** مع `expectedVersion` وidempotency key. يجب أن يرفض الخادم التحديث المتعارض بدلاً من الكتابة فوق نسخة أحدث، وأن يكتب audit record يتضمن المستخدم والوقت والفعل والكيان والحالة السابقة واللاحقة. لا ينبغي إضافة إعادة محاولة لعملية الحفظ إلا مع idempotency key، ولا ينبغي تخزين transcript مؤقتاً خارج حقل المسودة المطلوب.
