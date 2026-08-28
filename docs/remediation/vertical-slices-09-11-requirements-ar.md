# سجل متطلبات شرائح 09–11

**النطاق:** Hospital Core، Emergency/EMS/Prehospital Care، وNational Health Identity & Citizen Account. **البيانات اصطناعية فقط**، والتكاملات الخارجية interfaces/adapters مؤجلة؛ لا توجد claims إنتاجية.

## حدود الملكية غير القابلة للتفاوض

| الشريحة | تستخدم | لا تنشئ |
|---|---|---|
| 09 Hospital | Canonical Patient/Identity/Encounter/Medication/Orders/Clinical Record/Audit/Authorization | Patient أو Encounter أو Medication أو Order أو Record ثانياً داخل المستشفى |
| 10 Emergency/EMS | Canonical Patient/Identity/Encounter/Clinical Record/Medication/Lab/Imaging/Hospital/Audit | Patient أو Identity أو Encounter أو Clinical Record ثانية؛ temporary identity ليست Health ID أو National ID |
| 11 National Identity | NIAM Person/Identity/Account/Device/Session/Workspace، وCitizenLifecycle/Citizen كمالكين يحتاجان bridge واضحاً | NHID/Account/Device/Session/Consent/Record store ثانٍ فوق المالك الحالي |

## Slice 09 — Hospital Core

المسار المطلوب هو Admission → Bed → Ward/Care Team → Nursing → Vitals → Medication Administration/eMAR → Orders → OR/ICU/Transfer → Discharge → Unified Clinical Record. كل مورد يحتاج organization/facility/department/ward scope، status، version، metadata، FK/unique/check/index، object-level authorization، Idempotency-Key، If-Match، ACID transaction، row locks، append-only audit، وtyped errors.

Admission يدعم emergency/elective/transfer/observation وحالات `REQUESTED → ACCEPTED → ADMITTED → IN_CARE → DISCHARGE_PLANNED → DISCHARGED` مع cancelled/rejected/transferred. Bed يدعم available/reserved/occupied/cleaning/maintenance/blocked، وBedAllocation history لا يُحذف. يمنع proof التزامن تخصيص السرير نفسه مرتين ووجود active allocation مزدوجة للمريض.

CareTeam لا يمنح full record تلقائياً؛ يلزم purpose/relationship/workspace/scope. NursingTask له `OPEN → CLAIMED → IN_PROGRESS → COMPLETED` مع cancelled/deferred وone-winner claim. VitalObservation extensible ويحتفظ patient/encounter/observer/device/time/unit/method/source/version؛ القيم خارج expected range تحذر ولا تُرفض صامتاً إذا كانت صحيحة شكلياً.

MedicationAdministration يعيد استخدام Medication وPrescription من Slice 06، ويمر `ORDERED → VERIFIED → SCHEDULED → ADMINISTERED` مع held/refused/missed/cancelled، ويمنع duplicate administration ويحقق right patient/medication/dose/route/time دون اعتبار checklist بديلاً عن authorization. MedicationSafetyEvent يسجل الأخطاء دون حذف.

Hospital Orders تعيد استخدام canonical Clinical Order، وOR/ICU/Blood Bank تُنفذ فقط حيث توجد حدود آمنة قابلة للإثبات. يمنع OR تعارضات الزمن، ويحتاج checklist patient/procedure/site/consent/team قبل البدء، مع emergency override صريح إذا وُجد contract. Raw ICU/device telemetry منفصل عن Clinical Observation، ولا تتحول كل قراءة sensor تلقائياً إلى السجل.

Transfer يغلق allocation القديمة وينشئ الجديدة في transaction واحدة، ويمنع active allocation مزدوجة لنفس patient. Handover يحدّد minimal necessary data ويحتاج acknowledgement وفق policy. Discharge لا يكتمل قبل medication reconciliation وpending results/follow-up/instructions/summary/responsible provider؛ DischargeSummary الموقعة immutable والتصحيح إصدار جديد، والأحداث canonical تُسقط إلى Unified Clinical Record دون corruption أو last-write-wins.

## Slice 10 — Emergency/EMS/Prehospital

المسار هو Incident → Dispatch → Ambulance → Prehospital Assessment → Temporary Identity/Resolution → Treatment → Pre-alert → Hospital ED → Handover → Emergency Encounter → Admission/ICU → Unified Record. تُبنى contracts/adapters اصطناعية عند غياب EMS/GPS/dispatch/hospital integration، مع منع ادعاء وجود تكامل حقيقي.

EmergencyIncident وDispatchRequest/Assignment لهما idempotency وحالات صريحة، وEmergencyUnit/CrewMember يحتاجان identity/role/workspace/organization/unit/facility/credential/scope؛ membership وحدها لا تمنح clinical permission. GPS له minimum retention/purpose limitation/access control/audit ولا يصبح هوية للمريض أو مصدر authorization. يمنع object-level access بين incidents/units/hospitals.

TemporaryPatientReference فريد ومؤقت ومدقق ضمن incident، وليس Health ID أو National ID. Identity Resolution يعيد `MATCHED/MULTIPLE_MATCHES/NO_MATCH/REQUIRES_REVIEW`؛ الاسم أو OCR أو NFC أو biometric لا يكفي وحده، وAI ليس مصدر الحقيقة. عند mismatch لا يتم overwrite بل conflict/review/link event.

PrehospitalEncounter يُربط بالـincident وpatient/temp patient وcrew/unit ثم canonical Encounter عند handover بشكل idempotent. Triage وإعادة التقييم أحداث جديدة، والvitals تستخدم نموذج Hospital canonical. EMS medication/procedures تعيد استخدام MedicationAdministration وProcedure canonical، وتُسجل critical interventions بلا delete.

HospitalPreAlert له `CREATED → SENT → RECEIVED → ACKNOWLEDGED` مع failed/retrying، ويحتوي reference/incident/ETA/priority/summary/vitals/interventions/risks/destination. ETA estimate مع timestamp/source/confidence، destination policy-driven حسب capability/capacity وليس nearest hospital فقط. Handover correction amendment event، وBreak Glass منفصل عن consent، reason/scope/duration/actor/audit/notification إلزامية وtime-bounded.

Offline يسمح فقط بالـincident draft وtemporary patient وobservations/procedures المسموحة، ولا يسمح offline identity verification أو final clinical release أو controlled-medication approval. EMS Outbox event-id يجعل at-least-once transport ذات exactly-once logical effect، والمزامنة هي upload → server validation → conflict resolution → acknowledgement؛ لا last-write-wins.

## Slice 11 — National Health Identity & Citizen Account

يجب الفصل بين National Identity وHealth Identity وAccount Identity وProfessional Identity وWorkspace Identity وTemporary Emergency Identity. Health ID/NHID unique/stable/non-semantic/non-sequential/global وغير مشتق أو مكشوف كرقم وطني. Citizen/Resident/Visitor/Temporary Emergency Patient حالات مختلفة ضمن policy.

يُعاد استخدام NIAM Account/Identity/Person/Device/Session وCitizenLifecycle/Citizen بدلاً من إنشاء owners جديدة. Account state يدعم pending/verified/active وrestricted/suspended/locked/deactivated. One person/one health identity يُفرض deterministic/audited/idempotent؛ duplicate suspicion يذهب إلى possible duplicate/review/merged/rejected ولا يندمج آلياً.

IdentityEvidence وVerificationAttempt يسجلان النوع والمصدر والجهة والوقت والثقة والحالة. OCR/NFC/Selfie/Liveness/Government verification adapters منفصلة؛ OCR ليس verification، وNFC read ليس VERIFIED، وliveness ليس إثباتاً وحيداً، ولا تُخزن raw biometric templates في frontend. Provider down يعيد UNKNOWN/PENDING وليس VERIFIED. يمكن local verification profile فقط مع تسمية غير حكومية واضحة.

Professional role لا يتحول تلقائياً إلى citizen permissions. لكل شخص specialty أساسية واحدة مع أدوار/workspaces/organizations متعددة، وRole switch server-decided. Consent/share يعيدان استخدام access/consent owners القائمين مع purpose/scope/resources/start/expiry/revoke/history؛ family relation لا تعني full record، وguardian/minor تخضع policy.

Claims لا تحتوي clinical data، وتشمل sub/session/device/workspace/organization/permissions. refresh rotation وإعادة استخدام refresh token يؤديان إلى session-family revocation. OTP قصير العمر single-use rate-limited attempt-limited ولا يكشف وجود الحساب. recovery لا يتجاوز identity verification. Device trust يعتمد NIAM Device مع public key/secure keystore حيث يتاح، states new/challenged/verified/trusted وrevoked/compromised/expired.

Fraud/risk intelligence explainable/auditable/reviewable ولا يغلق مواطناً بسبب signal واحد. Identity changes أحداث immutable/outbox، evidence الحساسة مشفرة at rest مع KMS/HSM-capable boundary، وسياسات retention منفصلة للوثائق/selfie/OCR/audit/session/GPS. كل قرار provider أو fraud أو access يجب أن يكون قابلاً للمراجعة البشرية.

## أدلة إلزامية مشتركة قبل readiness

| البعد | الدليل المطلوب |
|---|---|
| Authorization | actor/session/membership + organization/facility/ward/unit/department + relationship/purpose/resource/action + IDOR/tenant tests |
| Integrity | state machine، If-Match/version، immutable correction/amendment، ACID وrow lock، no negative/duplicate active allocation |
| Reliability | durable idempotency/outbox، replay/conflict semantics، no last-write-wins، failure rollback |
| Audit | append-only canonical audit مع actor/time/action/entity/before/after أو event evidence، وminimal PHI |
| Database | additive migration، FK/unique/check/index، fresh upgrade ثم downgrade/re-upgrade على PostgreSQL disposable |
| Offline | allowlist صريحة، server validation بعد reconnect، conflict queue، منع final release/identity verification offline |
| External boundaries | interfaces/adapters فقط، synthetic providers، UNKNOWN/PENDING عند provider failure، لا credentials أو real health data |
| Performance | bounded queries، N+1 review، p50/p95/p99/error rate ضمن harness اصطناعي؛ لا cache mutable sensitive data لتجاوز authorization |
| Readiness | remote CI logs، staging smoke/rollback، API/worker concurrency، observability وfrontend E2E قبل production claim |

**ملاحظة المصدر:** الملف الأول ينتهي عند عنوان `MOBILE` في السطر 1468، والملف الثالث ينتهي عند بند Desktop في السطر 1392؛ المتطلبات المعروضة حتى هذه النقاط هي نطاق التنفيذ المتاح، ولا يجوز اختراع بنود غير موجودة في الملفات.

## سجل التحقق المنفذ في 2026-08-28

| الاختبار أو البوابة | النتيجة | حدود الدليل |
|---|---|---|
| focused Hospital/Emergency/Health Identity/DeviceGateway/Session/Contracts | `25 passed, 1 warning` | SQLite TestClient؛ لا يثبت multi-worker PostgreSQL API وحده |
| migration resilience وmigration tests | `19 passed, 1 warning` | يثبت chain guards المحلية؛ PostgreSQL proof موثق أدناه |
| Authentication regression + refresh-family tests | `7 passed, 1 warning` | يثبت lineage/replay semantics في unit/async stubs |
| full backend suite الحالي | `2831 passed, 5 skipped, 165 warnings` | نتيجة الشجرة الحالية؛ التحذيرات legacy/deprecation لم تُخفَ |
| PostgreSQL fresh upgrade | `20260828_0016 (head)` | قاعدة `gula_slices0911_test` محلية disposable فقط |
| PostgreSQL schema gate | `PASS` | تحقق من الجداول، session lineage columns، indexes، checks، وpermissions |
| PostgreSQL bed-lock primitive | `pass: conflict,winner` | دليل DB primitive؛ ليس اختبار API متعدد العمال |
| PostgreSQL generic row-lock primitive | `pass: conflict,winner` | جدول synthetic مؤقت أزيل بعد الاختبار |
| PostgreSQL downgrade/re-upgrade | `0016 → 0015 → 0016` | قاعدة اختبار محلية؛ لا rollback production |
| Engineering Inventory | `1976` ملفاً، `REPAIRING`, `production_ready=false` | inventory advisory، ووجود migration/اختبار لا يساوي جاهزية تشغيلية |

أُضيفت الآن مسارات provisioning للـward/room/bed وعضوية Care Team مع membership object check، ومسار manual reconciliation للهوية المؤقتة، وhandover/ePCR amendments كسجلات جديدة مرتبطة بـ`supersedes_id`، وDeviceGateway protocols/adapters اصطناعية لا تحفظ raw telemetry. كما أصبحت summary signing تعتمد `summary_version` بدلاً من `discharge.version`، وأصبح transfer allocation يتحرك حصراً عند `IN_TRANSIT → RECEIVED`، وأزيلت إضافة discharge المكررة.

تبقى التكاملات الحكومية وGPS والأجهزة وPACS/LIS/RIS/HIS وSMS/Telegram/WhatsApp وبيانات المواطنين الحقيقية خارج النطاق عمداً. كما لا يزال إثبات remote CI محجوباً عندما تعود runs بحالة `steps=[]`، ولا يوجد staging rollback أو frontend E2E جديد لهذه الشرائح؛ لذلك تبقى `golden_path_passed=false` و`production_ready=false`.
