# External Compatibility Notes

تم التحقق من وثائق المشروع الرسمي في [expo-speech-recognition](https://github.com/jamsch/expo-speech-recognition) و[إصداراته](https://github.com/jamsch/expo-speech-recognition/releases) بتاريخ 2026-08-18.

- الإصدار `3.0.0` يعلن دعماً رسمياً لـ Expo SDK 54.
- وثائق المشروع تميز بين `expo-speech-recognition@sdk-54` للإصدارات القديمة ونسخة `3.0.0` التي تدعم SDK 54.
- المكتبة تحتاج إلى config plugin وإلى Development Build عند استخدام native module؛ لا ينبغي افتراض أن Expo Go يحتوي الوحدة الأصلية.
- واجهات التحقق المستخدمة في GULA هي `isRecognitionAvailable()`, `supportsOnDeviceRecognition()`, `getSupportedLocales({})`, `getSpeechRecognitionServices()`, و`requestPermissionsAsync()`.
- خيارات الخصوصية المستخدمة هي `continuous: false`, `recordingOptions: { persist: false }`, و`requiresOnDeviceRecognition` فقط عندما يثبت توفر التعرف المحلي.
- مصدر API: https://github.com/jamsch/expo-speech-recognition/blob/main/src/ExpoSpeechRecognitionModule.types.ts
