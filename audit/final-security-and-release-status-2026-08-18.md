# GULA security and release status — 2026-08-18

## Executive status

تم دمج PRs #225 و#226 و#227 و#228 و#239 في `main`. آخر main المؤكد هو `7aa723d6b47b37d18666e9ed159999df92b5b2bd`، ويتضمن توحيد frontend-v3، mobile/PWA hardening، speech-to-text Expo، وNetty patch الأولي.

ظهر بعد الدمج أن Dependabot أعاد فحص `mobile-expo/package-lock.json` وفتح ثمانية تنبيهات جديدة بتاريخ 18 أغسطس. لذلك أُنشئ PR #241 على فرع `fix/mobile-expo-dependency-audit` لمعالجة الثمانية، وآخر head له هو `a0c87de09f55f3ac3635db2f4b0d75a60bec47a8`. PR #241 مفتوح وmergeable، لكنه `unstable` لأن بوابات GitHub Actions لم تُشغّل jobs فعلياً.

> لا يصح إعلان Dependabot = 0 على `main` قبل دمج PR #241. العدد الحالي الموثق على default branch هو **8 مفتوحة / 82 مغلقة**.

## Dependency remediation in PR #241

تم فرض PostCSS `8.5.26`، وuuid `11.1.1`، وMocha `10.8.2`. وبسبب عدم وجود patched npm release متاح لـimage-size مع كون upstream archived، أُضيف backport محلي محدود يحافظ على synchronous API المطلوب من Metro، ويرفض ICNS entry lengths الصفرية أو الخارجة عن حدود الملف، ويحافظ على zero-size box progress guard. أُضيف strict audit validator يرفض أي vulnerability بدلاً من allowlist مؤقتة، واختبار `npm run test:security` لمنع عودة infinite-loop DoS.

## Local verification

| Gate | Result |
|---|---|
| `npm ci --ignore-scripts` | Passed |
| `npm run typecheck` | Passed |
| `npm test -- --runInBand` | 4/4 tests passed |
| `npm run test:security` | Passed; malformed ICNS rejected without hanging |
| `npm audit --json` | 0 findings |
| `npm audit --omit=dev --json` | 0 findings |
| Expo public config safety validator | Passed |
| Expo Doctor | 17/17 checks passed |

## Current Dependabot inventory on main

| Alert | Package | Severity | Current manifest |
|---:|---|---|---|
| #478 | image-size — ICNS parser infinite loop | High | `mobile-expo/package-lock.json` |
| #477 | image-size — JXL/HEIF parser infinite loops | High | `mobile-expo/package-lock.json` |
| #474 | PostCSS — arbitrary file read via sourceMappingURL | High | `mobile-expo/package-lock.json` |
| #475 | PostCSS — source-map path traversal disclosure | High | `mobile-expo/package-lock.json` |
| #473 | uuid — missing buffer bounds check | Moderate | `mobile-expo/package-lock.json` |
| #476 | PostCSS — incomplete sourceMappingURL fix | Moderate | `mobile-expo/package-lock.json` |
| #471 | Netty — CORS Vary header cache poisoning/information disclosure | Moderate | `mobile/android/settings.gradle.kts` |
| #472 | PostCSS — XSS through unescaped `</style>` | Moderate | `mobile-expo/package-lock.json` |

## Code scanning status

صفحة Security and quality Overview توضح أن Code scanning alerts معطّل لأن GitHub Advanced Security متاح للـOrganizations فقط. الرابط القديم `/security/code-scanning` يعيد 404، لذلك لا يمكن استخدام الأرقام التاريخية السابقة كدليل على findings حالية أو إعلان remediation كامل لها من هذا repository الخاص. تفعيل Advanced Security على Organization مطلوب لتشغيل CodeQL وقراءة/إغلاق alerts الحالية.

## CI blocker

Run `32160563846` للـPR #241 فشل قبل تنفيذ الاختبارات. رسالة GitHub الرسمية كانت أن job لم يبدأ بسبب فشل دفعات الحساب مؤخراً أو الحاجة إلى رفع spending limit. Syntax Gate كان بلا خطوات، وبقية jobs كانت skipped وبلا خطوات. لذلك لا يوجد دليل على فشل الكود؛ توجد مشكلة billing/account تمنع runners.

Run: https://github.com/samertts/gula-platform/actions/runs/32160563846
PR: https://github.com/samertts/gula-platform/pull/241

## Production site verification

تم فتح `https://www.gula-platform.org/` بعد الدمج، وظهرت صفحة `/login` فعلياً مع دخول المواطن، دخول المؤسسات، selector للغات العربية والإنكليزية والكردية والتركمانية والسريانية، واختيار أدوار العرض التجريبي. تم فتح العرض التجريبي ووصل إلى dashboard معزول read-only ببيانات synthetic، مع حظر الكتابة والتكاملات الخارجية. كما أن `https://gula-platform.org/` يعيد التوجيه الصحيح إلى `https://www.gula-platform.org/login`.

## Required external action

لإنهاء الإطلاق الآمن: يجب على مالك GitHub معالجة `Settings → Billing & plans` أو spending limit للحساب/المؤسسة. بعد زوال الحظر، أعد تشغيل كل jobs في PR #241، وانتظر نجاح جميع required checks، ثم ادمج PR #241 فقط. بعدها انتظر دورة Dependabot، وتحقق من أن القائمة أصبحت 0 Open. إذا كان تشغيل CodeQL مطلوباً، فعّل Advanced Security على Organization أولاً؛ لا تستخدم admin bypass ولا تتجاوز required checks.
