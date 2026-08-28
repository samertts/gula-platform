# Ownership Mapping وADR تمهيدي لشرائح 09–11

**الحالة:** baseline بعد مراجعة الملفات الثلاثة والملاك الحاليين؛ لا يمثل production readiness.

## القرار المعماري

يُنفذ Hospital وEmergency فوق canonical clinical/NIAM كحدود additive فقط. لا تُمدد جداول legacy مباشرة ولا تُستخدم كبديل صامت للمريض أو اللقاء أو الوصفة أو السجل. تُعامل adapters الخارجية كواجهات synthetic-first، ويعيد provider failure حالات `UNKNOWN` أو `PENDING` ولا يرفع الثقة تلقائياً.

## مصفوفة المالكين

| المفهوم | المالك الحالي | قرار Slice 09–11 | المخاطر المكتشفة |
|---|---|---|---|
| Person/Identity/Account/Device/Session | `backend/app/identity/models/*` تحت `IdentityBase` | إعادة الاستخدام؛ لا second account/identity/device/session store | refresh الحالي يدور token JTI ويعطّل session القديمة لكنه لا يملك family lineage/reuse event كاملة |
| Citizen/health ID/guardian/consent-like lifecycle | `national_citizens` و`niam_lifecycle_citizen`/`GuardianAccount`/`FamilyLink`/`ConsentRecord` | bridge/extension تدريجي؛ لا NHID table موازي قبل قرار owner | `health_number` موجود وقد يكون sequential، وCitizenLifecycle يملك `health_id` وJSON consent/family، وخدماته تكتب status مباشرة بلا idempotency/If-Match موحد |
| Hospital hierarchy/bed/OR/checklist | `app/hospital/models/__init__.py` و`HospitalService` | canonical package جديد أو projection boundary؛ legacy يبقى isolated | IDs integer و`lab_id` و`current_patient_id` غير opaque؛ audit legacy؛ `SurgicalSafetyChecklist` يحتوي unique constraint على `lab_id` غير معرف في النموذج |
| EMS incident/dispatch/triage/ePCR | `app/ems/infrastructure/models.py` و`ems/application/service.py` | canonical emergency package جديد؛ لا توصيل مباشر بالـlegacy | commits مباشرة، lab-scoped ownership، legacy audit؛ لا temporary identity/pre-alert/handover/outbox canonical |
| Medication/Administration | Slice 06 canonical (`app/clinical/pharmacy`) | Hospital/EMS يعيدان استخدامه، ولا يخلقان medication DB ثانية | legacy pharmacy/EHR remain coexistence hotspots |
| Vitals/Observation | Slice 09 canonical owner بعد التنفيذ | EMS يعيد استخدامه | raw telemetry يجب أن يبقى خارج clinical record |
| Clinical Record/Access/Audit | `app/clinical/record` و`app/clinical/access` وcanonical audit | Hospital/Emergency/Identity تُسقط أحداثها إلى هذا المصدر | يجب منع draft/unreleased والتأكد من grant/break-glass policy |
| External verification/device gateways | `app/identity/services/verification_service.py` وlegacy gateway helpers | protocols + synthetic adapters فقط | gateway الوطني الحالي NON_CRITICAL؛ لا credential أو live provider في canonical tests |

## ضوابط التنفيذ

كل mutation الجديدة تتطلب actor/session/membership وسياق organization/facility/workspace/department/ward/unit/resource/action/purpose، ثم state machine وrow lock/ACID وdurable idempotency وIf-Match/version وappend-only audit. لا تُقبل client-derived patient/provider/status/tenant fields. التصحيح أو handover correction أو identity amendment يكون record/event جديداً لا overwrite.

الأولوية التنفيذية هي Hospital admission/bed/allocation/transfer/task/vitals/eMAR/discharge أولاً، ثم Emergency incident/dispatch/temporary reference/pre-alert/handover/outbox، ثم identity verification evidence/device/session hardening فوق owners NIAM. تُترك OR/ICU/Blood Bank وinsurance وgovernment/NFC/biometric الحقيقي كواجهات أو states آمنة فقط ما لم يوجد contract واختبار قابل للإثبات.

## عوائق معروفة يجب ألا تُخفى

لا تثبت اختبارات SQLite concurrency multi-worker. يلزم PostgreSQL disposable row-lock probe لكل مورد حساس، وfresh migration upgrade/rollback/re-upgrade، وremote CI قابل للقراءة. لا يُسمح أن يتحول نقص التكامل الخارجي إلى stub production أو `VERIFIED` وهمي. كما أن ملف Slice 09 ينتهي عند عنوان `MOBILE`، وSlice 11 ينتهي داخل قسم Desktop؛ لذلك لا تُخترع متطلبات غير موجودة في الملفات.

## قرارات hardening المنفذة

أُبقي Health ID مملوكاً لـ`CitizenLifecycle`، وأُنشئ `NiamHealthIdentityOperation` كسجل operation/evidence لا كمالك هوية جديد. Device وConsent وSession تستعمل NIAM owners القائمة. refresh tokens أصبحت مرتبطة بـfamily وparent JTI، ويؤدي replay المكتشف بعد rotation إلى إنهاء العائلة كاملةً، من دون تسجيل raw token.

أُضيفت طبقة Hospital canonical لتهيئة ward/room/bed وCare Team مع تحقق membership داخل organization/facility/workspace؛ لا يمنح Care Team full record تلقائياً. Emergency reconciliation لا يقوم بأي auto-match، بل يسجل MATCHED بموافقة صريحة أو PENDING_REVIEW/REJECTED. Signed ePCR وhandover corrections تنشئ records جديدة مع `supersedes_id` وسبب amendment، ولا تعدل الأصل الموقّع.

## حالة الدليل وحدوده

نجح full backend الحالي بـ`2831 passed, 5 skipped, 165 warnings`، ونجحت PostgreSQL disposable fresh upgrade/downgrade/re-upgrade إلى `20260828_0016` مع schema gate وprimitive row-lock proofs. هذه أدلة محلية اصطناعية؛ لا تثبت multi-worker API أو staging أو remote CI. يبقى `production_ready=false` و`golden_path_passed=false` إلى أن تتوفر أدلة remote CI وstaging/rollback وfrontend E2E وreview تشغيلي مستقل.
