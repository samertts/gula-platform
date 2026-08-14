# Mobile and Degraded-Mode Assessment

## النتيجة

لا توجد في المستودع حزمة React Native أو Expo مستقلة قابلة لتشغيل اختبارات JavaScript الخاصة بـIAM. يوجد مشروع Flutter فعلي تحت `mobile/desktop` مع طبقات `offline`, `database`, `sync_queue_manager`, `sync_engine`, `connectivity_service`, وsecure refresh-token storage، إضافة إلى مشاريع Android وiOS الأصلية.

هذا يعني أن حالة Mobile ليست `MISSING` على مستوى المصدر، لكنها ليست `verified` ضمن بوابة hardening الحالية لأن Flutter SDK غير متاح في sandbox؛ ولذلك تعذر تشغيل `flutter test --no-pub` آلياً. يجب تشغيل هذه الاختبارات في runner يحتوي Flutter SDK قبل إعلان mobile parity.

## عناصر موجودة في المصدر

| المتطلب | الدليل | حالة التحقق |
|---|---|---|
| تخزين offline | `mobile/desktop/lib/core/offline/database.dart` | موجود في المصدر؛ غير مشغل في هذه البوابة |
| Queue للمزامنة | `mobile/desktop/lib/core/offline/sync_queue_manager.dart` | موجود في المصدر؛ يحتاج Flutter tests |
| Retry/reconciliation | `mobile/desktop/lib/core/offline/sync_engine.dart` | موجود في المصدر؛ يحتاج اختبارات فشل/إعادة اتصال |
| Connectivity state | `mobile/desktop/lib/core/offline/connectivity_service.dart` | موجود في المصدر؛ يحتاج اختبار transitions |
| Offline UI | `gula_offline_banner.dart` و`gula_sync_indicator.dart` | موجود في المصدر؛ يحتاج widget tests |
| IAM workspace parity | لا يوجد دليل test فعلي مشترك مع NIAM Workspace API | غير مثبت |

## بوابة Flutter المطلوبة

يجب إضافة runner أو job منفصل يحتوي نسخة Flutter مثبتة ومقيدة، ثم تشغيل:

```text
flutter pub get
flutter analyze
flutter test --coverage
```

ويجب أن تشمل الاختبارات الدنيا queue enqueue/dequeue، retry exponential backoff، dead-letter behavior، reconnection auto-sync، duplicate idempotency key، conflict refusal، secure token rotation، وعدم السماح بعمليات غير حرجة في degraded mode.

## شرط الأمان

لا يجوز استخدام offline cache لإصدار قرار authorization أو الاحتفاظ بنتيجة سريرية mutable دون version check. أي عنصر offline يجب أن يحمل account/session/workspace context موثقاً، idempotency key، version، timestamp، وحالة reconciliation. تظل الموافقة السريرية والنتائج المعتمدة داخل GULA فقط.

إلى حين تشغيل Flutter CI وربط عقود Workspace المشتركة، التصنيف الصحيح هو **Mobile/degraded mode: SOURCE PRESENT, EXECUTION UNVERIFIED**، وليس Complete.
