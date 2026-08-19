# GitHub Dependabot status — 2026-08-20

After commit `d8d4805c`, GitHub Security displayed one open moderate Dependabot alert:

- Alert #471: `Netty Vulnerable to Cache Poisoning and Information Disclosure via CORS Vary Header Overwrite`.
- Detected dependency: `io.netty:netty-codec-http` (Maven).
- Manifest: `mobile/android/settings.gradle.kts`.
- GitHub states that Dependabot is creating a security update and that a manual upgrade to `io.netty:netty-codec-http` version `4.1.137.Final` or later is available.
- The page showed `1 Open` and `89 Closed` alerts while dependency-file checking for commit `d8d4805c` was still in progress.

The GitHub API request from the configured CLI returned HTTP 403 (`Resource not accessible by integration`), so this status was verified through the authenticated GitHub Security page.

This finding must be rechecked after GitHub finishes dependency-file analysis; if it remains open, the Android dependency constraint must be applied in the manifest Gradle configuration recognized by Dependabot, not only through a resolution strategy in another Gradle file.
