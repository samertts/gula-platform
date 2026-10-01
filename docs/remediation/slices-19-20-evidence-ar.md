# دليل Slice 19–20: بوابة التكامل الوطني والمسار الاصطناعي

## نطاق التنفيذ

تمت إضافة حد تكامل وطني **synthetic-only** بهدف تشغيل الاختبارات والعرض التجريبي دون اتصال بمزود حكومي أو شركة تأمين أو مصدر بيانات حقيقي.

الملفات الأساسية:

- `backend/app/gateways/national_integration_gateway.py`
- `backend/app/contracts/clinical_core.py`
- `backend/tests/test_national_integration_gateway.py`
- `.github/workflows/ci.yml`

## الضوابط المطبقة

1. **لا يوجد اتصال شبكي فعلي:** الـ provider الاصطناعي deterministic ولا يحتوي على HTTP client.
2. **رفض live وshadow:** حتى عند وجود متغيرات بيئية وطلب `live` أو `shadow`، يبقى النظام في وضع الرفض ولا يفتح اتصالاً.
3. **منع الحقيقة السريرية:** الحقول التي تحمل `clinical_truth` أو `diagnosis` أو `lab_result` أو `phi` تُرفض قبل تمريرها إلى provider.
4. **Idempotency:** كل كتابة تحتاج `idempotency_key`، وإعادة الطلب نفسه تعيد receipt محفوظاً، بينما إعادة استخدام المفتاح لطلب مختلف تُرفض.
5. **تحقق schema:** استجابة المزود يجب أن تكون synthetic ومحددة الحقول والحالة.
6. **الـ fallback معلّم:** الاستجابة الاحتياطية تحمل `requires_verification=True` عبر طبقة ExternalGateway.
7. **عقود حالات مركزية:** أضيفت عقود:
   - `national-integration-message`
   - `national-reconciliation`
   - `national-manual-review`
8. **فصل الاختبارات:** تم فصل `device_bridge` في CI عن backend لأن كلاهما يستخدم namespace باسم `app`، وتمت إضافة تقرير JUnit مستقل.

## دليل الاختبار المحلي

- Backend: `2842 passed, 5 skipped` بعد إضافة عقود واختبارات هذه الموجة.
- Device Bridge: `29 passed` بعد إصلاح الاختبارات الاصطناعية.
- الاختبارات المستهدفة للعقود والبوابة: `20 passed`.
- Golden Path الاصطناعي العابر للمجالات: `6 passed` مع إثبات انتقالات الموعد وEncounter والمختبر والنتيجة والمطالبة والبوابة الوطنية.
- الاختبار الجديد للموجة يثبت:
  - idempotency وعدم تغيير الطلب تحت المفتاح نفسه.
  - رفض payload سريري.
  - رفض live/shadow.
  - رفض الانتقال غير الصحيح في state machine.

## ما لم يُعلن جاهزيته

هذه الإضافة لا تعني جاهزية تكامل حكومي أو إنتاج وطني. ما زال يلزم قبل staging/production:

- PostgreSQL migration proof لأي جداول إضافية مستقبلية.
- اختبار تكامل مزود حقيقي بعد اعتماد رسمي وcredentialing منفصل.
- اختبار load/chaos وreconciliation على نطاق كبير.
- تشغيل Golden Path كامل عبر المواطن والمؤسسة والمختبر والتأمين.
- أدلة HA/DR وPITR وfailover ومراقبة 99.95%.

> أي بيانات تصل من النظام الاصطناعي هي بيانات اختبار فقط، ولا يجوز استخدامها لاتخاذ قرار سريري أو مالي حقيقي.
