# GULA deployment findings

## Vercel

- Project: `gula-platform`, team slug `samertts-projects`, project ID `prj_xvgrHcfO6BWlwViUJ6HRQdawPsKX`.
- Git repository: `samertts/gula-platform`, production branch `main`.
- Commit `6ffdad30` deployment failed because `npm install` exited with `ERESOLVE`.
- Commit `748b15ae26f862d78b3dabccad54f90d258aeec9` (`fix(deploy): resolve Vercel npm peer conflicts and isolate demo dashboard`) was deployed through the `production-main-recovery` hook and reached `READY`.
- The ready deployment URL returned by Vercel was `gula-platform-3h2qloj75-samertts-projects.vercel.app`; its aliases included `www.gula-platform.org`, `gula-platform.org`, and `gula-platform.vercel.app`.
- Direct browser testing on the deployment URL reached `/dashboard` after clicking the Demo button and showed `زائر العرض التجريبي`, `demo_viewer`, `بيئة عرض تجريبية`, and the isolated synthetic-data notice. This proves the published bundle's Demo flow works.
- Before the DNS change, Vercel Domains showed `www.gula-platform.org` as Valid Configuration and `gula-platform.org` as Invalid Configuration with a 308 redirect to `www.gula-platform.org`. After disabling Cloudflare proxy on the apex A record, Vercel temporarily showed `Failed To Load Cert` for both custom domains while certificate/DNS state propagates.

## Cloudflare

- Zone: `gula-platform.org`, zone ID `01df32adf2c890b7104741c031cef5a3`.
- Apex A record ID `b457066c4128c365de56d53aae7f9f47` had content `76.76.21.21` and was changed from `proxied: true` to `proxied: false` so Vercel can validate the apex target.
- `www.gula-platform.org` is a non-proxied CNAME to `f854d2b525458e11.vercel-dns-017.com`.
- Cloudflare DNS API returned HTTP 200 and `proxied: false` for the apex patch.

## Live behavior observed

- The Vercel deployment URL's root page loaded the GULA login page; visiting `/login` directly on the deployment URL returned 404, which is consistent with the SPA's root redirect/rewrite behavior and does not affect the root login flow.
- The old `www` browser session initially showed `حدث خطأ` after Demo because the browser had a stale service-worker/client state. The fresh deployment origin reached the dashboard successfully.
- `https://gula-platform.org` was previously serving an unrelated `My Google AI Studio App` response in the authenticated browser, while raw origin probing returned a Vercel `NOT_FOUND`; Vercel marked the apex configuration invalid. DNS correction is in propagation/certificate recovery.

## Source URLs

- Vercel project: https://vercel.com/samertts-projects/gula-platform
- Vercel deployments: https://vercel.com/samertts-projects/gula-platform/deployments
- Vercel domains settings: https://vercel.com/samertts-projects/gula-platform/settings/domains
- Ready deployment inspector: https://vercel.com/samertts-projects/gula-platform/57f9TjkxCiJSueuTrcSkf7cdMQ44
- Ready deployment URL: https://gula-platform-3h2qloj75-samertts-projects.vercel.app/
- Production site: https://www.gula-platform.org/
- Repository commit: https://github.com/samertts/gula-platform/commit/748b15ae26f862d78b3dabccad54f90d258aeec9
