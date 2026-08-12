# GULA Technical Leadership Decision Register

**التاريخ:** 2026-08-12

## Decisions that are already bounded

| القرار | الحالة | الحدود |
|---|---|---|
| `frontend-v3` canonical web | معتمد في Wave 2 | لا rename ولا حذف legacy frontends؛ أي freeze أو migration يحتاج inventory/build/route evidence. |
| GULA Account/NIAM as identity source | معتمد في Wave 2/Citizen C1 | لا duplicate citizen auth/account؛ legacy mapping قابل للعكس. |
| CitizenRelationship C1 | منفذ ومدفوع | additive فقط؛ لا backfill/dual-write/automatic activation. |
| Server-side authorization | غير قابل للتفاوض | frontend role guards UX فقط؛ كل resource access يحتاج relationship/policy/audit. |
| Demo isolation | غير قابل للتفاوض | synthetic data وDB/Redis/secrets/storage/connectors منفصلة؛ لا production bypass. |

## Decisions requiring explicit approval

| الموضوع | لماذا يحتاج اعتماداً | متطلبات القرار |
|---|---|---|
| Hosting: Hetzner/Contabo أو غيرهما | يغير sovereignty، network، backup، incident response، وdeployment behavior | data residency، threat model، RPO/RTO، cost/capacity، rollback، owner |
| Backup/restore service | قد يلمس PHI وsecrets ويغير retention | encrypted destination، key ownership، restore drill، retention/legal policy، operator access |
| Freemium/Pilot | قرار تجاري وتشغيلي وقانوني لا تقني فقط | SLA، support، entitlement، data processing، exit/rollback، facility cohort |
| Break-Glass activation | وصول عالي الحساسية وقد يؤثر على سلامة المرضى | allowed roles/reasons، step-up، expiry، notification، audit review، emergency policy |
| Legacy frontend freeze | يؤثر على مستخدمين ومسارات deployment | usage telemetry، migration owner، support window، rollback، no-delete rule |
| Native store release | release gate عالي المخاطر | security/privacy/accessibility/performance/offline/crash/recovery certification |

## Safe execution order

1. تنفيذ C2 relationship administration: create/review/activate/revoke، دون backfill أو auto-match، مع audit before/after وidempotency وnegative tests.
2. تنفيذ O1 backup/restore validation في بيئة معزولة دون تغيير production deployment.
3. تنفيذ I1 synthetic device bridge tests للـASTM/HL7/DICOM دون بيانات حقيقية.
4. تنفيذ O2 Break-Glass review والتفعيل فقط بعد approval.
5. تنفيذ F1 frontend inventory/consolidation evidence دون rename/delete.
6. تنفيذ M1 offline contract على بيانات غير حساسة أولاً ثم encrypted clinical cache بعد security review.
7. صياغة pilot charter، ثم cohort dry-run، ثم pilot controlled فقط بعد sign-off.

## Stop conditions

يتوقف التنفيذ إذا غابت provenance لعلاقة المواطن، أو لم يكن migration قابلاً للعكس، أو اختلف قرار authorization بين legacy وcanonical، أو تعذر إثبات Demo isolation، أو فشل restore، أو احتاجت التوصية تغيير deployment behavior دون اعتماد، أو ظهرت نتائج سريرية preliminary كأنها final.

## Current recommendation

تم تنفيذ C2 كدفعة تقنية للمراجعة، وتشمل audited relationship administration مع idempotency وscope validation وactivation/revocation. لا يعني ذلك اعتماد cohort production أو backfill أو dual-write. تبقى O1/I1/O2/F1/M1 وقرار نقل البنية إلى VPS أو freemium أو Break-Glass production أو store release خارج التنفيذ حتى تصدر الموافقات والأدلة المطلوبة. وجود Docker/Terraform/Helm وCI security workflows يثبت surfaces قابلة للفحص، لكنه لا يمثل موافقة تشغيلية ولا شهادة production readiness.
