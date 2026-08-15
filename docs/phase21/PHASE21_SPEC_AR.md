# GULA — Phase 21
## Health-Aware + Accessibility Adaptive Experience

### الحالة التنفيذية

تضيف هذه المرحلة مساحة موحدة داخل **Settings → Accessibility & Personal Needs**. تفصل المنصة بين إعدادات العرض والتفاعل منخفضة الحساسية وبين بيانات الاحتياجات الصحية الحساسة. لا تُستخدم أي قيمة صحية لتشخيص المستخدم أو تغيير دوره أو منحه Permission، ولا يقرر Frontend الوصول إلى أي مورد سريري.

| الوظيفة | الحالة | ملاحظة الإغلاق |
|---|---|---|
| Accessibility Profile في Backend | **READY** | تخزين persistent مع `lab_id` و`user_id` وversion وتدقيق hash-chain metadata. |
| Health Preferences في Backend | **READY** | payload مشفّر at rest، وموافقة صريحة، وسحب موافقة يحذف ciphertext. |
| Web/PWA Adaptive UI | **READY** | Context يطبق text scale وcontrast وreduced motion وcolor-blind metadata وtouch targets. |
| Web Health Preferences UI | **READY** | حقول اختيارية وموافقة واضحة وحالات Saved/Failed/Consent Required. |
| Android Accessibility | **READY** | حفظ محلي داخل `EncryptedSharedPreferences`; لا تُحفظ Health Preferences محليًا. |
| iOS Accessibility | **READY** | حفظ presentation-only عبر `UserDefaults` وThemeManager; لا تُحفظ Health Preferences محليًا. |
| Flutter Desktop Accessibility | **READY** | state container وواجهة Settings؛ لا تُحفظ Health Preferences محليًا. |
| Native Health Preferences عبر API | **BACKEND_DEPENDENCY** | يلزم ربط API client وواجهة consent الأصلية قبل السماح بإنشاء/عرض payload صحي على Android/iOS/Flutter. إبقاء الحقول خارج التخزين المحلي مقصود كإجراء حماية. |
| Voice interaction | **BLOCKED** | لا يُفعل قبل إضافة مزود صوت معتمد، consent مستقل، واختبار أمني وخصوصية. |
| ترجمة جميع نصوص Phase 21 إلى اللغات السبع | **BACKEND_DEPENDENCY** | الخيارات والقيم مدعومة في العقد؛ يلزم استكمال resource bundles ومراجعة لغوية قبل اعتماد النصوص النهائية. |
| مراجعة أمنية مستقلة | **SECURITY_REVIEW** | مطلوبة قبل الإنتاج النهائي، خصوصًا للتشفير وإدارة المفاتيح وaccess review. |
| مراجعة قانونية/امتثال | **LEGAL_REVIEW** | مطلوبة قبل تفعيل جمع Health Preferences في بيئة المستخدمين الحقيقيين. |

## Backend Data Model Specification

### `accessibility_profiles`

يحتوي السجل على `user_id` و`lab_id` و`preferences` بصيغة JSON محددة بعقد Pydantic، إضافة إلى `version` و`created_at` و`updated_at`. يضمن القيد الفريد وجود ملف واحد لكل مستخدم. تشمل الحقول اللغة، حجم النص، scale، high contrast، color-blind mode، screen-reader optimization، captions، visual alerts، reduced motion، touch targets، keyboard navigation، cognitive simplification، static alternatives، وتقليل الإشعارات.

### `health_preferences`

يحتوي السجل على `user_id` و`lab_id` و`encrypted_payload` فقط للمحتوى الصحي، مع `consent_granted` و`consent_version` و`consented_at` و`revoked_at` و`version`. لا تُكتب قيم الحساسية أو الحالات المزمنة أو نصوص المساعدة في AuditLog. عند سحب الموافقة يُضبط `encrypted_payload` إلى NULL وتُسجل عملية revoke دون المحتوى.

> **حدود البيانات:** Accessibility Preference ليست Health Condition وليست Medical Record. تفعيل قارئ الشاشة أو تكبير النص لا ينشئ تشخيصًا ولا يضيف Permission.

## Frontend Adaptation Rules

يقرأ `AccessibilityProvider` الملف بعد مصادقة المستخدم فقط. عند تعذر الشبكة يعمل العرض بالإعدادات الافتراضية ولا يحول فشل التفضيلات إلى قرار صلاحية. تُطبق التغييرات عبر CSS على الجذر: `--gula-text-scale` و`--gula-touch-scale` وclasses للتباين العالي وتقليل الحركة والقراءة الميسرة. تُحترم أيضًا `prefers-reduced-motion` في المتصفح.

لا تعتمد الحالات على اللون وحده. يجب أن يضيف أي مكون حالة دلالة نصية أو أيقونة أو شكلًا عند استخدام `data-status`. وتبقى المهام السريرية والصلاحيات والـScopes خارج Adaptive UI.

## Consent Model

لا يمكن حفظ Health Preferences إلا عند إرسال `consent=true` و`consent_version`. لا يمكن تحديث سجل موجود دون `version` مطابق؛ أي تعارض يعيد HTTP 409 ولا يطغى على تعديل أحدث. GET يعيد `consent_required` دون payload عندما لا توجد موافقة فعالة. DELETE يسحب الموافقة ويحذف ciphertext.

## Privacy Rules

يستطيع صاحب الحساب المصادق عليه الوصول إلى ملفه فقط عبر backend، مع مطابقة `user_id` و`lab_id` المستمدين من token/database وليس من حقول يرسلها Frontend. لا يوجد endpoint عام ولا وصول تلقائي للمختبر أو الطبيب. أي صلاحية مستقبلية لجهة مخولة يجب أن تمر عبر Consent/Policy/Scope مستقل وتدقيق صريح.

## Audit Events

تُسجل عمليات `updated` و`revoked` في `audit_logs` مع user، role، lab، resource type، الإصدار السابق واللاحق، حالة الموافقة، وIP. لا تتضمن التفاصيل payload الصحي. يستخدم التسجيل hash-chain القائم في GULA، ويجب أن تفشل العملية إذا فشل التدقيق وفق سياسة سلامة السجل.

## UX States

تستخدم الواجهة الحالات التالية: **default** عندما لا يوجد Accessibility Profile، **saved** عند وجود سجل، **consent_required** قبل عرض Health payload، **empty** قبل إنشاء السجل، **Saved** بعد النجاح، **Failed** عند فشل الحفظ، و409 عند تعارض version. أما Permission Denied وUnavailable فتظل حالات backend المعتمدة ولا تُحوّل إلى صلاحية محلية.

## Cross-platform QA Matrix

| المجال | 320/360/390/430px | 768/1024px | 1440/1920px | Android/iOS/Flutter |
|---|---:|---:|---:|---:|
| عدم قص العناوين والحقول | مطلوب | مطلوب | مطلوب | مطلوب |
| Keyboard/focus | مطلوب | مطلوب | مطلوب | بدائل platform-native |
| Text scaling 0.85–2.0 | مطلوب | مطلوب | مطلوب | Slider/native settings |
| High contrast | مطلوب | مطلوب | مطلوب | Native/local theme |
| Reduced motion/flashing | مطلوب | مطلوب | مطلوب | Native/local setting |
| Touch target ≥44px | مطلوب | حسب device | حسب device | مطلوب |
| RTL/LTR | العربية العراقية/الفصحى | Kurdish/Turkmen | English/Persian | حسب locale |
| Health payload plaintext local | ممنوع | ممنوع | ممنوع | ممنوع |

قبل اعتماد النشر يجب تنفيذ اختبار بصري فعلي على جميع المقاسات المذكورة، واختبار Keyboard-only وScreen Reader وColor-blind simulation وReduced Motion. بناء الويب الحالي ينجح typecheck/build/PWA generation، بينما بناء Android/iOS/Flutter يحتاج بيئة أدوات المنصات المقابلة.

## بوابات الاعتماد قبل الإنتاج

يجب أولًا تشغيل migration `20260815_0019_phase21_user_preferences` على staging والتحقق من rollback في نسخة قاعدة بيانات اختبارية. ثم يجب التأكد من وجود `ENCRYPTION_KEY` إنتاجي مُدار عبر Railway Secret وليس قيمة مثال. بعد ذلك تُنفذ مراجعة صلاحيات وpenetration test للـendpoints الأربعة، وتُراجع resource bundles للغات السبع، ثم يُنشر PR عبر حماية `main` مع جميع checks. لا يُنشر أي تطبيق إلى متجر ضمن هذه المرحلة.
