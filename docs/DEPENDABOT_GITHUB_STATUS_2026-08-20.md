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
