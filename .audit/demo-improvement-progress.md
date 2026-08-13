# GULA Demo Improvement Progress

## External CI/Vercel findings

- Pull Request: https://github.com/samertts/gula-platform/pull/128
- Branch: `feature/demo-personas`
- Vercel project: `gula-platform`, project ID `prj_xvgrHcfO6BWlwViUJ6HRQdawPsKX`, team `samertts' projects` (`team_P8pcOYC97mQiBdr6UEG0osai`).
- The preview deployment for commit `a840e0d9` reached Vercel state `READY`.
- GitHub workflow `Frontend - PWA Build & Deploy` failed at the Lighthouse job because `.github/workflows/frontend-pwa.yml` referenced `GoogleChrome/lighthouse-ci-action@v12`; GitHub reported that the repository could not be resolved.
- Verified via GitHub CLI that `treosh/lighthouse-ci-action` exists, then changed the workflow reference to `treosh/lighthouse-ci-action@v12` and pushed commit `0e4fdb7f`.
- After the workflow fix, GitHub checks were still in progress; Vercel continued reporting a deployment rate-limit failure and Vercel API returned no deployment after the latest timestamp. This is treated as an external deployment-service limitation, not a local build failure.
- Local verification after the demo changes: backend demo/security tests passed (8 tests), frontend typecheck passed, the demo Vitest file passed (2 tests), and the frontend production build passed.

## Safety boundary

The demo environment remains synthetic and read-only. No production data, secrets, MX/TXT records, or production branch were changed.
