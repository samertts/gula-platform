# GULA Citizen Test Plan

## C1 evidence

| Gate | Evidence |
|---|---|
| Python compile | `python3 -m compileall` على route/model/migration نجح |
| Relationship unit tests | 8 tests passed: scope، missing scope، expiry/revocation، path-ID، own-context، ambiguity، write scope |
| Backend full suite | `2301 passed, 251 warnings` |
| Fresh migration | SQLite upgrade من empty إلى `20260811_0002 (head)` نجح |
| Rollback | downgrade إلى `20260811_0001` ثم re-upgrade إلى head نجح |
| Web | frontend-v3 typecheck وproduction build نجحا |

## Required future suites

تشمل account registration/verification/recovery/MFA/session/device، Health ID/linkage/collision، own/unauthorized/guardian/delegate/expired/revoked/workspace-switching، IDOR/token misuse/tenant isolation/data leakage، final-only result states، appointments/queue/radiology/pharmacy/referrals/documents/vaccination، offline stale/sync/conflict/recovery، RTL/screen-reader/forms/errors، low-end/low-bandwidth، و10 end-to-end journeys المحددة في التوجيه.

لا تنتقل الموجة التالية عند أي cross-citizen leakage أو authorization divergence أو missing audit أو preliminary result exposure أو build failure. كل test failure يعالج بجذر السبب قبل commit.
