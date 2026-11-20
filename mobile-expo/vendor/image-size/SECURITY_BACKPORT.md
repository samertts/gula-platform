# image-size security backport

This vendored package is derived from `image-size@1.2.1` and retains the original MIT license. It exists only because the upstream repository was archived on 2026-06-03 and the GitHub-reviewed advisories for ICNS, JXL, and HEIF parser denial of service currently list no patched npm release.

| Advisory | Affected range | Backport control |
|---|---:|---|
| GHSA-w3rx-r6r6-pgpr / CVE-2025-71330 | `<= 2.0.2` | Reject ICNS files and entries whose declared lengths are smaller than the header or exceed the input/file boundary. |
| GHSA-5p2g-fcmc-qvqq / CVE-2025-71329 | `<= 2.0.2` | Preserve the zero-size box progress guard in `dist/types/utils.js`; every box scan advances or terminates. |

The package keeps the synchronous API required by Metro 0.83.3 and is selected through the root `overrides` map. PostCSS is pinned to `8.5.26`, which includes source-map path protection, and uuid is pinned to `11.1.1`, which backports the buffer-bounds fix. Mocha is pinned to `10.8.2` for the development graph. The clean install and both production/full `npm audit` reports contain zero findings.

The regression command is `npm run test:security`. It constructs a malformed ICNS buffer with a zero-length entry and asserts that parsing rejects it in under one second instead of hanging. This vendor should be removed when Metro/Expo publishes a compatible release that includes the upstream fixes; until then, changing or bypassing the override is a security-sensitive change requiring a new regression test.

References: [GitHub Advisory GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr), [GitHub Advisory GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq), [PostCSS 8.5.26 release](https://github.com/postcss/postcss/releases/tag/8.5.26), [uuid 11.1.1 release](https://github.com/uuidjs/uuid/releases/tag/v11.1.1).
