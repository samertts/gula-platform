# حالة Code Scanning وDependabot في GULA — 2026-08-26

## النتيجة التنفيذية

يحتوي المستودع على workflowين متشابهين لـCodeQL (`codeql.yml` و`codeql-analysis.yml`). هذا يسبب تشغيل تحليلين لنفس لغتي Python وJavaScript/TypeScript، وقد ينتج فئات SARIF متنافسة أو فشلاً مكرراً. تم في هذا الفرع الاحتفاظ بـ`CodeQL Advanced` كـworkflow وحيد، ونقل trigger الخاص بفروع `release/*` إليه، وحذف workflow القديم المكرر. لم تُحذف أي لغة من المصفوفة، وبقيت صلاحية `security-events: write` على job التحليل.

## حدود خدمة GitHub الحالية

المستودع خاص، وواجهة REST أعادت أن `security_and_analysis` غير متاحة عبر التكامل الحالي، بينما تعرض صفحة Code Scanning أن الخدمة غير مفعلة للمستودع. لذلك لا توجد قائمة Code Scanning مفتوحة يمكن إغلاقها من داخل المستودع الآن. وجود workflow في `.github/workflows/codeql.yml` يجهز الفحص عند توفر GitHub Advanced Security أو الخطة التي تسمح به، لكنه لا يفعّل الخدمة ولا يثبت أن نتائج SARIF وصلت إلى GitHub.

تشغيل CodeQL الأخير كان يفشل خلال ثوانٍ وبلا steps منفذة على الفرع `fix/mobile-expo-dependency-audit`. هذا النمط لا يثبت وجود ثغرة في كود التطبيق؛ ويجب تأكيد السبب من إعدادات GitHub أو صلاحيات الخطة/runner قبل تغيير منطق التحليل. لم يتم تعطيل الفحص لتجميل الحالة، ولم يتم تشغيل bypass.

## Dependabot #471

يبقى تنبيه Netty رقم #471 ظاهراً في صفحة Dependabot بمستوى Moderate، مع أن `origin/main` وPR #241 وPR #247 تحتوي تثبيت `io.netty:netty-codec-http:4.1.137.Final`. أظهر الفحص المحلي لـGradle أن `buildEnvironment` يحل Netty إلى `4.1.137.Final` بنجاح، وأن `debugAndroidTestRuntimeClasspath` لا يحتوي dependency مطابقة مباشرة لأن التأثر موجود في buildscript/UTP classpath.

التنبيه مرتبط بـCVE-2026-59903 وGHSA-8c42-7qj2-3j46، والإصدار المصحح المعروض في GitHub هو `4.1.137.Final`. تم تنفيذ Refresh Dependabot من واجهة GitHub، وظهرت رسالة أن إعادة الفحص وُضعت في الطابور وأن الفحص جارٍ لcommit `c36b4a4`. لم يتم dismiss أو suppress للتنبيه؛ تبقى حالة GitHub server-side غير مؤكدة إلى أن تنتهي عملية الفحص.

## فحوصات محلية

أظهر `npm audit` الكامل، بما فيه devDependencies، صفراً من الثغرات في lockfiles التي تم فحصها: root و`frontend-v3` و`mobile-expo` وTypeScript SDK وMinistry وPharmacy وplatform/ui. وأظهر `pip-audit` صفراً من الثغرات المعروفة في ملفات requirements المفحوصة. هذه النتيجة لا تستبدل فحص Dependabot أو CodeQL ولا تعني اعتماداً إنتاجياً.

### مراجع

- [CodeQL Advanced workflow](../../.github/workflows/codeql.yml)
- [صفحة Dependabot في GitHub](https://github.com/samertts/gula-platform/security/dependabot)
- [تنبيه Dependabot #471](https://github.com/samertts/gula-platform/security/dependabot/471)
- [توثيق Security Hardening](../../.github/workflows/security-hardening.yml)
