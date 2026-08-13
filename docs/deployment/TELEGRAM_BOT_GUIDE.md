# دليل تفعيل وربط بوت تليغرام (Telegram Bot Guide) لمنصة GULA

يتيح هذا الدليل تفعيل خدمة **Telegram Bot** لمراقبة المنصة بالكامل، تلقي التنبيهات السريرية الحرجة فور حدوثها، وإرسال النتائج المخبرية تلقائياً.

---

## 1. خطوات إنشاء البوت عبر Telegram
1. فتح تطبيق تيليغرام والبحث عن المساعد الرسمي: **@BotFather**.
2. إرسال الأمر `/newbot` واتباع التعليمات لتسمية البوت (مثال: `GulaHealthBot`).
3. ستقوم بالحصول على **Bot Token** (مثال: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
4. الحصول على **Chat ID** الخاص بك عبر بوت مثل **@userinfobot** أو إرسال رسالة للبوت ثم زيارة الرابط:
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` لمعرفة رقم الـ `chat_id`.

---

## 2. إعداد المتغيرات البيئية (Environment Variables)
قم بإضافة المتغيرات التالية إلى ملف التكوين أو بيئة التشغيل على السيرفر:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

---

## 3. اختبار الاتصال عبر الواجهة الخلفية
يمكنك اختبار إرسال التنبيهات الفورية عبر استدعاء نقطة النهاية الآمنة:
```http
POST /api/v1/telegram/test-alert
```
سيقوم البوت بإرسال تقرير فوري لحالة المنصة والتنبيهات السريرية إلى حسابك على التيليغرام مباشرة.

## 4. صلاحية المحادثة الخاصة بالمالك فقط

يجب ضبط `TELEGRAM_ADMIN_USER_ID` على **المعرّف الرقمي لحسابك في تيليغرام**، وليس اسم المستخدم. هذا الحساب وحده يستطيع إرسال رسائل إلى المنصة واستلام ردودها. بقية الحسابات يمكنها استقبال التنبيهات المرسلة من المنصة، لكن أي رسائل واردة منها تُهمل دون رد.

```bash
export TELEGRAM_ADMIN_USER_ID="123456789"
export TELEGRAM_WEBHOOK_SECRET="ضع-سرًا-عشوائيًا-طويلًا-هنا"
```

بعد نشر المنصة، اضبط webhook مرة واحدة:

```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${BASE_URL}/api/v1/telegram/webhook" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"
```

## 5. إنشاء حساب المالك الأعلى

لا تُحفظ كلمة المرور داخل المستودع. من مجلد `backend` شغّل أداة التهيئة عبر متغيرات مؤقتة:

```bash
export OWNER_NAME="اسم المالك"
export OWNER_EMAIL="owner@example.com"
export OWNER_PASSWORD="كلمة-مرور-قوية-لا-تقل-عن-12-حرفًا"
export OWNER_LAB_NAME="GULA Platform"
python -m scripts.bootstrap_owner
```

الحساب يُنشأ بالدور `master_admin` ويكون فعالًا مباشرة. تسجيل الدخول يتم عبر `POST /login` من الواجهة أو عميل API باستخدام البريد وكلمة المرور، وبعدها تُحفظ جلسة الدخول في cookie آمنة. لأن دور `master_admin` مميّز، يجب إكمال إعداد المصادقة متعددة العوامل من قسم MFA قبل أول دخول فعلي.

> لا تستخدم بيانات المثال كما هي، ولا ترسل كلمة المرور أو رمز MFA إلى تيليغرام.
