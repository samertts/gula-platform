# دليل أتمتة النشر المستمر (CI/CD) لتطبيق أندرويد GULA

يوضح هذا المستند خطوات إعداد وتفعيل مسار العمل (GitHub Actions) لبناء حزمة الإنتاج الموقعة (`.app bundle / .aab`) ورفعها تلقائياً إلى **Google Play Console**.

---

## 1. المفاتيح السرية المطلوبة في GitHub Secrets

يجب إضافة الأسرار التالية في إعدادات المستودع على GitHub تحت المسار:
`Settings -> Secrets and variables -> Actions -> New repository secret`

| اسم السر (Secret Name) | الوصف |
| :--- | :--- |
| `ANDROID_KEYSTORE_BASE64` | محتوى ملف Keystore (`gula-production.jks`) مشفر بصيغة Base64. |
| `ANDROID_KEYSTORE_PASSWORD` | كلمة مرور ملف الـ Keystore (`GulaHealth2026Secure!`). |
| `ANDROID_KEY_ALIAS` | اسم مفتاح التوقيع (`gula-release-key`). |
| `ANDROID_KEY_PASSWORD` | كلمة مرور مفتاح التوقيع (`GulaHealth2026Secure!`). |
| `PLAY_SERVICE_ACCOUNT_KEY` | محتوى ملف JSON الخاص بحساب الخدمة (Service Account) لـ Google Play Console مشفر بصيغة Base64. |

---

## 2. كيفية توليد Base64 لملف Keystore

لتشفير ملف التوقيع وتحويله إلى نص يمكن وضعه في GitHub Secrets، تنفيذ الأمر التالي في الحاسوب المحلي:

```bash
base64 -w 0 mobile/android/app/keystore/gula-production.jks
```

ثم نسخ الناتج ولصقه في قيمة السر `ANDROID_KEYSTORE_BASE64`.
