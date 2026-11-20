# Dependabot alert #471 — current evidence

## Finding

| Field | Current evidence |
|---|---|
| Repository | `samertts/gula-platform` |
| Package | `io.netty:netty-codec-http` (Maven) |
| Manifest | `mobile/android/settings.gradle.kts` |
| Severity | Moderate, CVSS 6.5 |
| CVE | CVE-2026-59903 |
| GHSA | GHSA-8c42-7qj2-3j46 |
| Affected versions | `<= 4.1.136.Final` |
| Patched version | `4.1.137.Final` |
| Status observed on GitHub | **Open** |

GitHub describes the issue as a Netty `CorsHandler` behavior that can overwrite an existing `Vary` header, creating cache-poisoning and information-disclosure risk in affected deployments. The transitive path shown by GitHub is `com.google.testing.platform:core:0.0.9-alpha04` → `com.android.tools.utp:android-test-plugin-host-emulator-control:32.3.1` → `io.netty:netty-codec-http:4.1.136.Final`.

Source: <https://github.com/samertts/gula-platform/security/dependabot/471>

## Remediation present on PR #241

The current `fix/mobile-expo-dependency-audit` head contains explicit `4.1.137.Final` resolution pins in `mobile/android/settings.gradle.kts`, `mobile/android/build.gradle.kts`, and `mobile/android/app/build.gradle.kts`. The app/root Gradle files also pin the related Netty HTTP/2, handler, proxy, and codec modules to the patched line, and the app declares `io.netty:netty-codec-http:4.1.137.Final` directly.

This is evidence that the remediation is present on the PR branch; it is not evidence that the default branch alert has closed. The alert remains open because PR #241 has not been merged and the GitHub Dependabot security-update job reports that no self-hosted runner was available. The page offers a patched version but no dismissal was performed.

## Current release decision

The repository's latest push notice reports one moderate vulnerability on the default branch, linking to alert #471. PR #241 must not be merged while required CI is unavailable. After the repository owner restores GitHub Actions billing/spending eligibility and the Dependabot update job can run, all required checks must be rerun against the latest head. The alert should be considered closed only after GitHub rescans the default branch and confirms closure; manual dismissal is not an acceptable substitute.

## Verification date

The live Dependabot alert page was checked on 2026-08-23. The page showed `Open`, patched version `4.1.137.Final`, and the runner-unavailable message. The PR head verified locally at that time was `2b47d7741e280811460506d5514abc8d44920dd5`.
