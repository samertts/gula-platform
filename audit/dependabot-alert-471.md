# Dependabot alert #471 — evidence

- **Repository:** `samertts/gula-platform`
- **Package:** `io.netty:netty-codec-http`
- **Manifest:** `mobile/android/settings.gradle.kts`
- **Severity:** Moderate, CVSS 6.5
- **CVE:** CVE-2026-59903
- **GHSA:** GHSA-8c42-7qj2-3j46
- **Affected range:** `<= 4.1.136.Final`
- **Patched version:** `4.1.137.Final`
- **Transitive path:** `com.google.testing.platform:core:0.0.9-alpha04` → `com.android.tools.utp:android-test-plugin-host-emulator-control:32.3.1` → `io.netty:netty-codec-http:4.1.136.Final`
- **Issue:** Netty `CorsHandler` can overwrite an existing `Vary` header, enabling cache poisoning and information disclosure in affected deployments.
- **GitHub state at 2026-08-18:** Open; GitHub reports that Dependabot is creating a security update from PR #222. The page also states that a manual upgrade to `4.1.137.Final` or later is available.
- **Source:** https://github.com/samertts/gula-platform/security/dependabot/471

## Dependabot state after main merge

بعد دمج PR #239، أظهرت قائمة Dependabot في GitHub **8 تنبيهات مفتوحة** و82 مغلقة. بقي #471 مفتوحاً، وظهرت تنبيهات جديدة في `mobile-expo/package-lock.json`: #478 و#477 لـ`image-size`، #474 و#475 و#476 و#472 لـ`postcss`، و#473 لـ`uuid`. لذلك لم يتحقق شرط 0 open بعد؛ تحديث Netty في main لم يغلق alert في فحص Dependabot الحالي، وتحتاج شجرة Expo SDK 54 إلى مسار معالجة مستقل أو ترقية SDK مدروسة.

**List URL:** https://github.com/samertts/gula-platform/security/dependabot

## Security UI verification

قائمة Dependabot بعد الدمج تعرض 8 تنبيهات مفتوحة و82 مغلقة، بينها #471 وسبعة تنبيهات npm جديدة في `mobile-expo/package-lock.json`. أما الرابط القديم `https://github.com/samertts/gula-platform/security/code-scanning` فأعاد GitHub صفحة 404، لذلك لا يمكن اعتباره دليلاً على عدم وجود CodeQL alerts؛ يلزم استخدام Security and quality > Overview أو واجهة CodeQL الجديدة للوصول إلى findings الحالية.

## Code scanning availability

صفحة Security and quality Overview الجديدة توضّح أن **Code scanning alerts: Disabled** لأن Advanced Security متاح للـOrganizations فقط. لذلك فإن أرقام CodeQL التاريخية المذكورة في السياق السابق لا يمكن التحقق منها من واجهة هذا repository الحالية، ولا يمكن إغلاقها من هذه الصفحة دون تفعيل Advanced Security على مستوى Organization.

**Overview URL:** https://github.com/samertts/gula-platform/security
