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
