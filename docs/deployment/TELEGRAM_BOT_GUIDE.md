# دليل تشغيل Telegram Bot بأمان

يتيح هذا الدليل تفعيل **Telegram Bot** للتنبيهات التشغيلية والسريرية الحرجة ضمن ضوابط المصادقة والتفويض. لا تضع أي رمز أو كلمة مرور حقيقية داخل المستودع أو ملفات الواجهة الأمامية.

---

## 1. إنشاء البوت والحصول على Chat ID

استخدم **@BotFather** لإنشاء البوت، ثم احصل على Chat ID الإداري من رسالة واردة للبوت أو من قناة داخلية موثوقة. يجب استخدام Chat ID رقمي، وليس اسم المستخدم.

لا تستخدم `getUpdates` أو أي أداة تعرض التوكن في سجل shell مشترك. خزّن التوكن في Secret Manager أو متغير بيئة محمي.

## 2. متغيرات التشغيل المطلوبة

اضبط المتغيرات التالية على الخادم أو مزود النشر فقط:

```bash
export TELEGRAM_BOT_TOKEN="<bot-token>"
export TELEGRAM_ALLOWED_CHAT_IDS="<admin-chat-id>"
export TELEGRAM_WEBHOOK_SECRET_TOKEN="<random-secret-at-least-32-bytes>"
```

يمكن استخدام `TELEGRAM_CHAT_ID` كبديل متوافق لمعرف واحد، لكن `TELEGRAM_ALLOWED_CHAT_IDS` هو الخيار المفضل للإنتاج. لا تُرسل `TELEGRAM_BOT_TOKEN` أو `TELEGRAM_WEBHOOK_SECRET_TOKEN` إلى المتصفح أو Telegram أو ملفات السجل.

## 3. تسجيل Webhook مع Telegram

استخدم نفس قيمة `TELEGRAM_WEBHOOK_SECRET_TOKEN` في حقل `secret_token` عند تسجيل webhook. لا تضع القيمة الفعلية في سجل الأوامر؛ استخدم Secret Manager أو ملف عملية محمي.

```bash
curl --fail-with-body --silent --show-error -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  --data-urlencode "url=${BASE_URL}/api/v1/telegram/webhook" \
  --data-urlencode "secret_token=${TELEGRAM_WEBHOOK_SECRET_TOKEN}"
```

يتحقق backend من الترويسة `X-Telegram-Bot-Api-Secret-Token` باستخدام مقارنة ثابتة الزمن، ويرفض أي Chat ID غير موجود في allowlist. إذا لم يكن secret أو allowlist مضبوطاً، يُغلق المسار fail-closed ولا يعالج الأوامر.

## 4. صلاحيات الأوامر والتنبيهات

يتطلب `POST /api/v1/telegram/test-alert` جلسة GULA مصادقاً عليها بدور `master_admin` أو `ministry_admin`. لا يُعد هذا المسار health check عاماً ولا يجوز نشره دون مصادقة.

الأوامر الواردة من Telegram تُقبل فقط من Chat IDs المصرح بها. يجب تقليل بيانات المرضى في التنبيهات إلى الحد الأدنى، وعدم إرسال أرقام وطنية أو رموز وصول أو كلمات مرور أو تفاصيل غير لازمة عبر الرسائل.

## 5. التحقق بعد النشر

تحقق من حالة webhook باستخدام واجهة Telegram من بيئة إدارية محمية، ثم اختبر رسالة تشغيلية اصطناعية فقط. لا تُرسل نتيجة مريض حقيقية في اختبار التكامل. راجع سجلات GULA للتأكد من تسجيل حالات الرفض للـ secret غير الصحيح والـ Chat ID غير المصرح به دون كشف قيم الأسرار.

إذا ظهر خطأ `503 Telegram webhook is not configured`، فلا تُخفّض الحماية؛ اضبط المتغيرات المطلوبة في Secret Manager ثم أعد تشغيل الخدمة. وإذا ظهر `403`، راجع التطابق الحرفي للـ secret وChat ID المصرح به.
