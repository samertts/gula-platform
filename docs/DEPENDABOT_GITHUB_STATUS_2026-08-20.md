# GitHub Dependabot status — 2026-08-20

After commit `d8d4805c`, GitHub Security displayed one open moderate Dependabot alert:

- Alert #471: `Netty Vulnerable to Cache Poisoning and Information Disclosure via CORS Vary Header Overwrite`.
- Detected dependency: `io.netty:netty-codec-http` (Maven).
- Manifest: `mobile/android/settings.gradle.kts`.
- GitHub states that Dependabot is creating a security update and that a manual upgrade to `io.netty:netty-codec-http` version `4.1.137.Final` or later is available.
- The page showed `1 Open` and `89 Closed` alerts while dependency-file checking for commit `d8d4805c` was still in progress.

The GitHub API request from the configured CLI returned HTTP 403 (`Resource not accessible by integration`), so this status was verified through the authenticated GitHub Security page.

This finding must be rechecked after GitHub finishes dependency-file analysis; if it remains open, the Android dependency constraint must be applied in the manifest Gradle configuration recognized by Dependabot, not only through a resolution strategy in another Gradle file.


## Follow-up after commits `ed2a395e` and `20504436`

The authenticated GitHub Security page still displayed `1 Open` and `89 Closed`, with alert #471 remaining Moderate. GitHub was still showing dependency-file checking in progress for the earlier analyzed commit, so the status is not yet a completed post-scan result for `20504436`. The page continues to identify the transitive path through `com.google.testing.platform:core 0.0.9-alpha04` and `com.android.tools.utp:android-test-plugin-host-emulator-control 32.3.1`, with affected Netty `4.1.136.Final` and patched `4.1.137.Final`.

Source: https://github.com/samertts/gula-platform/security/dependabot/471


## Forced refresh

On 20 August 2026, the repository's authenticated GitHub Security page was used to select **Refresh Dependabot alerts**. GitHub confirmed: `Refresh queued, it may take several minutes to see changes reflected in your alerts.` The alert was intentionally not dismissed; its open state remains the source of truth until the refreshed dependency graph confirms the patched version.


## Refreshed scan status

After the forced refresh, GitHub now reports: `Dependency file check in progress for commit e7652fe…`. The page still shows `1 Open` and `89 Closed`, with alert #471 listed as Moderate. This confirms that the refresh is analyzing the latest default-branch commit rather than the previously stale `d8d4805` graph; the result is still pending.

Source: https://github.com/samertts/gula-platform/security/dependabot


## Post-wait verification

After an additional wait, the GitHub page still reports `Dependency file check in progress for commit e7652fe…` and still lists `1 Open` / `89 Closed`. The scan has not produced a final alert state yet.


## Extended-wait verification

After a further two-minute wait, GitHub still reports `Dependency file check in progress for commit e7652fe…`; the list remains `1 Open` and `89 Closed`, and alert #471 remains Moderate. The repository-side Gradle graph is patched and verified, but GitHub's server-side scan has not returned a final state yet.


## Third extended-wait verification

After an additional three-minute wait, GitHub still reports `Dependency file check in progress for commit e7652fe…` and continues to list `1 Open` / `89 Closed`. No final result has been published by GitHub yet.


## Local remediation applied

Because GitHub identifies `mobile/android/settings.gradle.kts` as the manifest for the UTP path, the patched release is now declared directly in that settings buildscript classpath and forced there as `io.netty:netty-codec-http:4.1.137.Final`. The existing root and app-level constraints remain in place, so the actual Gradle build classpath and project configurations resolve the patched version.

Local gates after this change: `npm run test:security` passed; Gradle `help` and `buildEnvironment` passed and showed Netty `4.1.137.Final`; Ruff on changed Python files passed; `git diff --check` passed. GitHub server-side status remains pending until the refreshed scan completes.


## After d41057d8

The settings-level Netty pin was pushed to `main` as commit `d41057d8`, and local Gradle gates passed. GitHub's Dependabot page, however, still displays the prior `Dependency file check in progress for commit e7652fe…` message and the same `1 Open` / `89 Closed` counts. The page has not yet reflected the new commit or produced a final result for alert #471. GitHub's push hook also reported one moderate vulnerability, so the alert remains open and is not being marked closed by assumption.


## GitHub refresh limit

The Dependabot management menu now reports: `Refresh Dependabot alerts — Refreshed recently, available again in about 1 hour.` Therefore another manual refresh cannot be triggered at this time. The page still shows the stale in-progress check for `e7652fe` and `1 Open`; no UI action was used to dismiss or suppress the alert.


## Follow-up after PR #241 remediation — 21 August 2026

After resolving PR #241 conflicts and pushing commit [`17b234d5`](https://github.com/samertts/gula-platform/commit/17b234d5ea512da6065ef531340f25077d9a79f2), the locked `mobile-expo` installation passed `npm audit` with zero findings. The security parser regression test, typecheck, and Expo Doctor also passed. Three invalid Python exception clauses in the transformation engine were corrected, and the Alembic graph was normalized after a duplicate revision and two independent heads were discovered.

GitHub REST API verification showed PR #241 on branch `fix/mobile-expo-dependency-audit` at SHA `17b234d5ea512da6065ef531340f25077d9a79f2`, with `mergeable=true` and `mergeable_state=unstable` while published checks are pending. Attempts to read Check Runs and Combined Status for this SHA returned HTTP 403 `Resource not accessible by integration`. This does not prove published CI success and does not change the state of Netty alert #471; the GitHub page must be rechecked after the billing/spending-limit or integration-permission issue is resolved.
