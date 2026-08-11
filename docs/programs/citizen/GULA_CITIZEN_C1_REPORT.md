# GULA Citizen C1 Report — Relationship and API Hardening

**التاريخ:** 2026-08-11

**الحالة:** Implemented, committed, and pushed to the Wave 3 review branch.

**Commit:** `c5b630f91218729127f5c0fcb2a62282b6c4b5e0`

**Remote branch:** `wave3-identity-dependency-hardening-20260811`

## Scope

تثبت هذه الدفعة أساس العلاقة الصريحة بين حساب/حساب legacy والمواطن أو المريض، وتحمي Citizen Platform API من الوصول المعتمد على معرف يختاره العميل. لا تنفذ backfill أو dual-write أو merge أو تغيير deployment behavior.

## Implemented

| Area | Change |
|---|---|
| Identity foundation | `CitizenRelationship` additive model تحت NIAM مع source kind، relationship type، scope، status، validity، verification، expiry، revocation، version، وmetadata. |
| Migration | `20260811_0002_citizen_relationship_foundation.py` ينشئ جدولاً جديداً فقط مع foreign keys/check constraints/indexes وdowngrade. |
| Authorization | `require_citizen_relationship` يرفض default، يتحقق من active/unexpired/unrevoked relationship وresource scope، ويدعم own-context `/me/*` مع رفض ambiguity. |
| Audit | كل citizen-platform access decision يسجل success/denial وresource/method/reason عبر audit service دون raw PHI. |
| API | أضيفت own-context routes: `/me/dashboard`, `/me/profile`, `/me/health-summary`, `/me/appointments`, `/me/medications`, `/me/lab-results`. |
| Web | أضيفت `frontend-v3` صفحة ومسار `/citizen` للمواطن، مع إبقاء `/citizen-platform` الإداري قائماً دون rename أو حذف. الصفحة تستخدم own-context endpoints. |
| Documentation | أضيفت وثائق architecture, identity, account, workspace, authorization, verification, consent, privacy, data, API, offline, security, test, release، وgap/plan. |

## Evidence

| Gate | Result |
|---|---|
| Python compile | نجح على route/model/migration. |
| C1 targeted tests | `8 passed`، وتشمل missing scope، expiry/revocation، own context، ambiguity، cross-context path، وwrite scope. |
| Fresh SQLite migration | نجحت من قاعدة فارغة إلى `20260811_0002 (head)`. |
| Migration rollback drill | downgrade إلى `20260811_0001` ثم re-upgrade إلى `20260811_0002 (head)` نجح. |
| Backend full suite | `2301 passed, 251 warnings`؛ التحذيرات موجودة في أجزاء قائمة وليست failures. |
| frontend-v3 | typecheck وproduction build نجحا بعد إضافة صفحة/route/permissions/i18n. |
| Git safety | لم تُلمس ملفات `.audit/ci-fix.patch` و`.audit/ci-repair.patch` غير المتتبعة، وبقيت خارج commit. |

## Residual risks and next gates

لا تزال العلاقة canonical account-to-citizen تحتاج workflow تحقق/activation وcohort dry-run؛ C1 لا تنشئ relationships تلقائياً. المسارات القديمة ذات `/{citizen_id}` compatibility محمية الآن بالrelationship guard لكنها ليست العقد العام المستهدف، ويجب تقليصها لاحقاً بعد migration/read-only comparison. لم تُثبت بعد final-only clinical projections لكل domain، guardian/delegation workflow، Demo citizen seed isolation، offline encrypted sync، native release builds، أو AI governance.

لا يُعلن Citizen Application مكتملة، ولا تُنفذ store release أو production rollout أو branch/release operations قبل بوابات C2–C17 والمراجعات المطلوبة.
