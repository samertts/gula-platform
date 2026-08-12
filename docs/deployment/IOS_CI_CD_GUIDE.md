# دليل أتمتة النشر المستمر (CI/CD) لتطبيق iOS لنظام GULA

يوضح هذا المستند متطلبات إعداد مسار العمل (GitHub Actions) لبناء حزمة الإنتاج لنظام iOS (`.ipa`) ورفعها تلقائياً إلى **TestFlight / App Store Connect**.

---

## 1. المفاتيح السرية المطلوبة في GitHub Secrets

يجب إضافة الأسرار التالية في إعدادات المستودع على GitHub تحت المسار:
`Settings -> Secrets and variables -> Actions -> New repository secret`

| اسم السر (Secret Name) | الوصف |
| :--- | :--- |
| `IOS_BUILD_CERTIFICATE_BASE64` | شهادة التوزيع (`.p12` Distribution Certificate) مشفرة بصيغة Base64. |
| `IOS_P12_PASSWORD` | كلمة مرور ملف شهادة الـ `.p12`. |
| `IOS_PROVISION_PROFILE_BASE64` | ملف البروفايل (`.mobileprovision`) مشفر بصيغة Base64. |
| `IOS_KEYCHAIN_PASSWORD` | كلمة مرور عشوائية لإنشاء مفتاح التشغيل المؤقت في الـ Runner. |
| `APP_STORE_CONNECT_USERNAME` | بريد حساب Apple ID المرخص لـ App Store Connect. |
| `APP_STORE_CONNECT_PASSWORD` | كلمة مرور التطبيق المخصصة (App-Specific Password) من appleid.apple.com. |
| `APP_STORE_CONNECT_TEAM_ID` | معرف الفريق (Team ID) الخاص بحساب المطور في Apple. |

---

## 2. خطوات تفعيل النشر التلقائي

1. رفع علامة إصدار (Git Tag) تبدأ بحرف `v` (مثال: `v1.0.0`) ودفعها للمستودع:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. سيبدأ مسار العمل في GitHub Actions تلقائياً بـ:
   - فحص وكتابة الكود (SwiftLint & Tests)
   - بناء وحزم التطبيق بنجاح (`Archive & Export IPA`)
   - الرفع التلقائي إلى TestFlight عبر `xcrun altool`.
