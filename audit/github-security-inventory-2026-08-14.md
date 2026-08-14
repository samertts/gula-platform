# GitHub Security inventory — 2026-08-14

The GitHub Dependabot page for `samertts/gula-platform` reports **45 open alerts** and **331 closed alerts**. The dependency files were checked 10 hours ago for commit `6405bbb`.

The visible open findings include one critical Bouncy Castle advisory, multiple high-severity Netty advisories, JDOM2 XXE, jose4j compressed-JWE DoS, Apache Commons Compress memory exhaustion, and a direct Python `cryptography` advisory in `backend/requirements-lock.txt` (alert #120). The alerts are concentrated in `mobile/android/settings.gradle.kts` and the backend lockfile.

The page navigation reports **1,916 Code Scanning alerts**. GitHub API access from the sandbox returned HTTP 403 (`Resource not accessible by integration`), so the authenticated browser dashboard is the authoritative source currently available for inventory.

No alert was dismissed, closed, or modified.

The Code Scanning page reports **1,916 open alerts** and **710 closed alerts** on `main`. GitHub displays a banner: **CodeQL is reporting errors**. The first visible open findings include four critical `Partial server-side request forgery` alerts in `backend/.../integration/testing.py` at lines 427, 392, 357, and 228. Visible high findings include clear-text logging of sensitive information in `backend/.../gateways/residency_gateway.py`, `scripts/quality_gate.py`, `scripts/constitution_enforcer.py`, and `contracts/.../gula/client.py`; insecure SSL/TLS version in `.audit/check_security_headers.py`; and uncontrolled data used in path expressions across certification, contracts, and API files. No alert was modified.

After revisiting the dashboard, GitHub now reports **42 open Dependabot alerts / 334 closed** and **376 open Code Scanning alerts**. The Bouncy Castle alert #310 detail is marked **Fixed** with patched version `1.80.2`, indicating that GitHub is actively reprocessing the repository and the earlier counts were stale. The Dependabot list still labels its dependency snapshot as commit `6405bbb`, so the dashboard may lag behind `main` tip. No alert was modified.

Dependency detail checks: Netty alert #291 reports `io.netty:netty-codec-http2` patched at `4.1.132.Final` (the current forced version `4.1.118.Final` is insufficient). JDOM alert #287 reports `org.jdom:jdom2` patched at `2.0.6.1`; the repository already forces `2.0.6.1`, so that alert should clear after the dependency snapshot refreshes. The Bouncy Castle alert #310 is fixed at `1.80.2`; the repository currently forces `1.80` and should be raised to `1.80.2`.

Additional dependency detail checks: Kotlin Gradle Plugin alert #321 is patched at `2.4.20-Beta1`, while the project currently uses `2.1.20` and KSP `2.1.20-1.0.31`. Maven metadata currently exposes KSP versions only through the 2.3.x line in this environment, so an unverified Kotlin/KSP jump would risk breaking Android builds; the safer immediate mitigation is disabling Gradle build cache (`org.gradle.caching=false`) until a compatible Kotlin/KSP pair is validated. Commons Compress alert #276 is patched at `1.26.0`, which the project already forces; it should clear after dependency refresh.

CodeQL detail review: alert #2621 flags `print(_redact(output))` in `scripts/quality_gate.py`; alert #2618 flags `print(_redact(json.dumps(report, ...)))` in `scripts/constitution_enforcer.py`. Both are `py/clear-text-logging-sensitive-data` findings. The fix is to emit only allowlisted status metadata and counts rather than raw subprocess/report details, because regex redaction is not a sufficient proof for CodeQL or clinical log safety.

After pushing commit `d658088d`, the Code Scanning dashboard now shows **170 open alerts / 2,456 closed**, down from 376 open / 710 closed during the previous snapshot. The page still shows a CodeQL reporting-errors banner and lists alerts from the pre-refresh snapshot, including the files changed in the new commit; the new CodeQL runs are queued on GitHub. This indicates the alert database is actively being reprocessed, but final closure counts must wait for the queued runs to finish.

A second remediation patch also hardened `backend/core/api/main.py` by replacing the user-derived PDF filename with an OS-generated temporary filename, and removed API-key environment-name logging from `backend/app/ai_fabric/gateway.py` plus entity identifiers from `backend/app/ai/guardrails.py`. The latest local security subset passed **33/33 tests** and the modified Python files compile successfully. These changes are pending the next GitHub push and CodeQL refresh.

Post-CodeQL refresh: the dashboard decreased to **164 open / 2,470 closed**, but CodeQL created new alerts for the sanitizer functions themselves. Alert #2632 flags `Path(path).resolve()` in `_safe_output_path()` because the function still accepts a user-provided path before validation. This requires a stricter API that accepts only an allowlisted report identifier or server-created path, rather than attempting to sanitize arbitrary user paths after construction.

After CodeQL Advanced and CodeQL Analysis both completed successfully for `a02f7957`, the authenticated dashboard currently reports **357 open / 2,277 closed** and still displays the `CodeQL is reporting errors` banner. The new top findings are no longer the path alerts fixed in the latest commit; they are broader legacy findings across scripts, contracts, apps, and platform packages (for example weak hashing, missing rate limiting, clear-text logs, and insecure randomness). This confirms the latest scan completed but the repository still contains a wider security backlog that must be triaged by production reachability rather than claimed as fully remediated.


## Latest authenticated browser snapshot after e031281a

The My Browser snapshot of `https://github.com/samertts/gula-platform/security/dependabot` showed **41 open** and **335 closed** Dependabot alerts. The first page listed `mobile/android/settings.gradle.kts` as the Maven manifest for the visible findings. High-severity examples included `org.jdom:jdom2`, multiple `io.netty` modules (`netty-codec-http2`, `netty-handler`, `netty-codec-http` and `netty-codec`), and `org.bitbucket.b_c:jose4j`; a moderate direct alert was visible for `org.jetbrains.kotlin:kotlin-gradle-plugin`. The repository security navigation showed Code Scanning **2,055**, conflicting with the earlier Code Scanning page snapshot of 147 open alerts; this discrepancy must be rechecked after the next CodeQL run and with the active filter state verified.

The GitHub API attempt to list Dependabot alerts returned HTTP 404, and an explicit GET attempt returned HTTP 403 `Resource not accessible by integration`; the authenticated browser dashboard is therefore the current inventory source.

## Current uncommitted remediation changes

The current working tree contains the following security changes that still require local verification, commit, push, and fresh GitHub scans: the Python SDK no longer logs URL paths and its sanitizer was removed; OAuth2 token hashing and partner API-key hashing use HMAC-SHA512 with server secrets and constant-time comparison; constitution and quality-gate output is reduced to allowlisted status/count metadata; demo password documentation no longer persists passwords; Ministry KPI trend parsing no longer uses replacement-based string handling; citizen and UI email validation use bounded linear checks; the TypeScript SDK normalizes base URLs without regex; both OAuth server cores use `express-rate-limit`; both Vite server cores rate-limit Vite and static/fallback requests; and `express-rate-limit@^7.5.0` was added to both app manifests with pnpm metadata updated where available.


## Node 24 and Kotlin advisory verification

The official `actions/checkout` page states that its current Node24-compatible line requires Actions Runner v2.327.1 or newer. Public GitHub API release/commit lookups resolved the current Node24-compatible action commits used in this patch: checkout v7.0.1 at `3d3c42e5aac5ba805825da76410c181273ba90b1`, setup-python v7.0.0 at `5fda3b95a4ea91299a34e894583c3862153e4b97`, and setup-node v7.0.0 at `820762786026740c76f36085b0efc47a31fe5020`.

The GitHub-reviewed advisory `GHSA-r937-wjx7-w2jp` / `CVE-2026-53914` confirms `org.jetbrains.kotlin:kotlin-gradle-plugin` is affected before `2.4.20-Beta1` and patched at `2.4.20-Beta1`. The Android project currently uses Kotlin `2.1.20`, so this dependency requires a compatibility decision with KSP before changing the plugin line.


Dependabot alert #289 detail confirms `org.bitbucket.b_c:jose4j` is affected before `0.9.6` and patched at `0.9.6`; the Android build already forces `0.9.6`. The alert is transitive through `com.android.tools.build:gradle 8.13.2`, so it should close after GitHub refreshes the dependency snapshot.


## CI follow-up after rebasing on remote main

Remote `main` advanced to `6cb9e014` with IAM and Dependabot merges. The security commit was rebased safely and pushed as `88b4958f`. Initial CI exposed three independent regressions: the IAM route test did not unwrap the repository's lazy `_IncludedRouter` wrappers; migration `20260814_0005` seeded IDs longer than the declared `varchar(26)` columns; and Flutter formatting reported one changed Dart file.

The official Android migration guide confirms AGP 9 has built-in Kotlin, requires removing `org.jetbrains.kotlin.android`, and states that `org.jetbrains.kotlin.kapt` is incompatible with built-in Kotlin; it recommends KSP or `com.android.legacy-kapt` when KSP migration is not yet possible. The official Hilt Gradle setup currently documents Hilt `2.60.1` with KSP and the Hilt Gradle plugin. The Android build is therefore being migrated to AGP 9-compatible plugin wiring rather than reintroducing the obsolete Kotlin Android plugin.


## Android manual verification

Manual `Mobile - Android CI/CD` dispatch on `5c90d6bb` confirmed the AGP 9/Hilt plugin migration and dependency graph submission, but `lintDebug` initially failed at AAR metadata because `androidx.hilt:hilt-navigation-compose:1.4.0` and lifecycle 2.11.0 required API 37 while CI provisions compileSdk 35. The official AndroidX Hilt release notes confirm that requirement. The app now pins `hilt-navigation-compose` to 1.3.0, whose AAR metadata declares minCompileSdk 35; local Gradle dependencyInsight resolves lifecycle runtime Compose to 2.9.4 for the Android-test runtime classpath with no 2.11.0/API37 indicator. This keeps the current SDK boundary explicit instead of raising compileSdk without provisioning the matching SDK.


## Kotlin advisory verification

GitHub Advisory `GHSA-r937-wjx7-w2jp` / CVE-2026-53914 marks `org.jetbrains.kotlin:kotlin-gradle-plugin` versions `< 2.4.20-Beta1` as affected and `2.4.20-Beta1` as patched. The Android project uses Kotlin `2.4.20-RC`, which is above the patched floor. The AndroidX Hilt release notes at https://developer.android.com/jetpack/androidx/releases/hilt state that the 1.4.0 Compose integration requires API 37; artifact metadata inspection showed Hilt navigation Compose 1.3.0 requires minCompileSdk 35, so the app was pinned to 1.3.0 while retaining Dagger Hilt 2.60.1.


## Annotation processor follow-up

The Android lint retry on `431890c2` passed AAR metadata but failed during `kaptDebugKotlin` with `java.lang.IllegalStateException: Could not parse metadata! Try bumping kotlinpoet and/or kotlinx-metadata version.` The same log warns that Moshi Kotlin Code Gen KAPT support is deprecated and recommends KSP. Android's official AGP migration guide recommends KSP under built-in Kotlin, while the official Hilt Gradle setup documents Hilt 2.60.1 with KSP. GitHub's Kotlin advisory `https://github.com/advisories/GHSA-r937-wjx7-w2jp` sets the patched floor at Kotlin 2.4.20-Beta1; the project Kotlin plugin is 2.4.20-RC. KSP artifact metadata currently exposes 2.2.x and 2.3.x plugin lines, so the next Android fix must choose a verified KSP/Kotlin pairing rather than guess a non-existent 2.4.20 KSP version.


## Official KSP guidance

Android's official migration guide at https://developer.android.com/build/migrate-to-ksp recommends migrating supported processors from KAPT to KSP and explicitly lists Dagger, Room and Moshi as libraries with KSP support. The Kotlin KSP overview lists Moshi and Room as officially supported and notes Hilt support as in progress. Google KSP release 2.3.10 includes a fix for AGP 9 built-in Kotlin R-class resolution, and release 2.3.11 is the current latest release at the time of verification. The Android lint failure is specifically from Moshi KAPT metadata parsing. The current patch migrates Moshi code generation to KSP 2.3.11 while leaving Hilt and Room on legacy KAPT for an incremental, reversible verification; GitHub CI must confirm the processor graph before any further processor migration.
