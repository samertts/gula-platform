# Baseline موجة Vertical Slices 02B–05

## الغرض

يوثق هذا الملف نقطة البداية قبل تنفيذ المتطلبات المرفقة الخاصة بـSlice 02B، وLaboratory Core في Slice 03، وLab Result Core في Slice 04، وClinical Result Access & Sharing في Slice 05. النطاق هو **BUILD / REMEDIATION / HARDENING / DEVELOPMENT** فوق البنية canonical القائمة، وليس إعلاناً عن جاهزية إنتاجية.

> البيانات الصحية الحقيقية، وPHI، وcredentials، والتكاملات الحكومية أو HIS/LIS/RIS/PACS أو أجهزة analyzer أو SMS/WhatsApp/Telegram الإنتاجية ممنوعة في هذه الموجة. Synthetic Backend يبقى للاختبارات فقط، وBackend هو مصدر الحقيقة الوحيد للتفويض والكتابة.

## نقطة Git والبيئة

| العنصر | الحالة المقاسة |
|---|---|
| Repository | `samertts/gula-platform` |
| Branch | `feat/citizen-journey-20260827` |
| HEAD | `7a9b10eb2079c0e8ae06d991d00dc6946fff0fdd` |
| PR | #250، `OPEN` و`Draft`، base `fix/external-ingestion-dmz-er-20260825` |
| Python | 3.12.3 |
| Node.js | 22.13.0 |
| PostgreSQL proof runtime | 16.15 disposable محلياً؛ متوقف بعد cleanup |
| Redis proof runtime | 7.0.15 disposable محلياً؛ متوقف بعد cleanup |
| Migration head | `20260827_0012`، مع forward compatibility guard |
| Full backend baseline | `2797 passed, 5 skipped, 165 warnings in 308.37s`، exit code `0` |
| Frontend baseline | frontend-v3 اجتاز محلياً test/lint/typecheck/build/bundle budget في الموجة السابقة؛ لم تُفتح Live clinical writes |

## الموجود الذي سيُعاد استخدامه

المسار canonical المثبت هو:

`Identity → Session → Workspace → Authorization → Appointment → Check-in → Queue → Encounter → Clinical Note → Audit`

يجب أن يعاد استخدام NIAM و`AppointmentAuthorizationService` و`SyncCanonicalAuditService` و`DomainError` وidempotency/version/error patterns بدلاً من بناء framework سريري منفصل لكل مجال. كما توجد طبقات legacy للمختبر والنتائج في `app/services/order_service.py` و`app/routes/results.py` و`app/routes/test_results.py`. هذه الطبقات تحتوي أجزاء مفيدة مثل optimistic locking وcatalog lookup، لكنها ليست canonical Slice 03–05 لأنها تستخدم scoping وRedis idempotency وpublic-token sharing وتعرض مخاطر duplicate model/route وPHI overexposure؛ ستبقى خلف حدود واضحة إلى أن تتم مراجعتها.

يوجد أيضاً `NiamConsentService` و`consent_dep.py` كقاعدة server-authoritative أولية للمشاركة، مع expiry وscope وaudit. لكنهما لا يثبتان بعد متطلبات Slice 05 الكاملة: purpose/resource granularity، organization/facility/workspace context، `If-Match`، idempotency receipts، access history، ومصفوفة provider/grantee.

## مصفوفة متطلبات المرفقات

| الموجة | الهدف | الحالة عند baseline | سياسة التنفيذ |
|---|---|---|---|
| Slice 02B | إثبات Check-in → Queue → Encounter → Clinical Note على PostgreSQL/Redis مع API وconcurrency وE2E وperformance وrollback | **PARTIAL**: local API وPostgreSQL primitive وRedis shared-controls مثبتة؛ remote CI يفشل قبل steps، ولا يوجد staging/API load/browser E2E كامل | إغلاق الأدلة القابلة للتنفيذ أولاً، مع إبقاء readiness سلبية عند غياب staging/CI |
| Slice 03 | Encounter → Lab Order → Specimen → Accession → Collection → Processing | **NOT_STARTED_CANONICALLY**: توجد legacy lab/order/sample models وخدمات، ولا توجد حزمة canonical كاملة | تصميم فوق Core نفسه، migration additive، state machine، contextual authorization، idempotency، If-Match، chain of custody، بدون analyzer حقيقي أو offline writes |
| Slice 04 | Specimen → Result → Technical Validation → Clinical Validation → Critical Result → Release | **NOT_STARTED_CANONICALLY**: توجد legacy `LabResult` وroutes، ولا توجد Result Core canonical كاملة | فصل domain model عن FHIR، server policy للvalidation/release، immutable corrections/amendments، notification event synthetic فقط |
| Slice 05 | Doctor Review → Citizen Access → Share → Revoke → Access History | **PARTIAL_FOUNDATION**: consent v2 وconsent dependency موجودان، لكن grant/access history/context/idempotency غير مكتملة | توحيد الموجود أو إنشاء additive canonical grant فقط بعد فحص duplicate ownership، مع expiry افتراضي، purpose/scope، If-Match، audit، وdeny-by-default |

## ضوابط غير قابلة للتفاوض

كل كتابة سريرية يجب أن تمر عبر transaction وcontextual/object/tenant authorization وstate machine وaudit وidempotency وoptimistic concurrency حيث يلزم. لا يعتمد النظام على `role == doctor` أو إخفاء زر في الواجهة. لا يثق backend بـ`patient_id` أو `organization_id` أو `facility_id` أو `status` أو `created_by` القادم من العميل إذا كانت هذه الحقول server-controlled.

لا يفتح العمل offline clinical writes أو analyzer/LIS/RIS/PACS أو government identity/NFC/liveness أو production notifications. أي notification مستقبلية تمر عبر event/outbox وprovider abstraction ولا تجعل transaction تنتظر مزوداً خارجياً. لا تُعدّل نتيجة أو note released/signed مباشرة؛ يلزم correction/amendment جديد مع سبب وإصدار وتدقيق.

## بوابات الانتقال

لا تنتقل الموجة إلى frontend Live write أو mobile write أو production-like claim قبل تحقق API direct tests، negative IDOR/tenant tests، transaction-failure tests، deterministic concurrency، migration/rollback، query/performance evidence، وstaging مصرح به. تبقى `golden_path_passed=false` و`production_ready=false` حتى يثبت remote CI القابل للقراءة وstaging smoke وrollback rehearsal والتشغيل التشغيلي.

## المخاطر المعروفة

| الخطر | الأثر | المعالجة المبدئية |
|---|---|---|
| legacy lab/result duplicate models/routes | تضارب في authorization أو schema أو semantics | Inventory detector، owner canonical واحد، وعدم فتح route جديد قبل map/reuse |
| public result tokens/history | enumeration أو إفراط في عرض PHI | إبقاء المسارات legacy خلف policy، وعدم إعادة استخدامها لـCitizen Access الجديد |
| migration history drift | فشل أو schema غير متوافق في قواعد سبق أن سجلت revision | forward guard 0012 يرفض drift الخطِر؛ أي cast أو DDL إصلاحي يحتاج data audit ومراجعة مستقلة |
| Redis outage | تجاوز rate limit/idempotency/revocation إذا تم fallback صامت | production/staging fail-closed، وdegraded mode صريح ومراقب فقط |
| CI failure بلا steps | لا يمكن إثبات فشل التطبيق عن بعد | لا تعطيل ولا continue-on-error؛ توثيق external runner blocker وطلب إصلاح قابل للقراءة |
| frontend optimistic privilege | تجاوز قواعد الخادم أو كشف draft/unreleased data | backend authorization والـDTO projection مصدر الحقيقة، وfrontend read-only حتى اكتمال الأدلة |

## القرار التالي

تبدأ الخطوة التنفيذية التالية من Slice 02B gaps القابلة للإثبات: API/multi-process concurrency وtransaction-failure proof وqueue policy وcross-actor tests وlimited browser E2E إن توفرت بيئة disposable. بعد تثبيت ذلك، يبنى Lab Core canonical بالتدرج: **LabOrder ثم Specimen/Accession/Collection ثم Processing**، ثم Result Core، ثم Access/Sharing. لا تُعتبر أي موجة ناجحة لمجرد وجود models أو unit tests؛ لكل موجة تقرير evidence مستقل وتصنيف `PASS` أو `PARTIAL` أو `FAILED` أو `BLOCKED` أو `EXTERNAL_DEPENDENCY`.

## تحديث التنفيذ الحالي — 2026-08-28

تم تنفيذ أول مسار canonical قابل للتشغيل لـSlice 03–05 فوق Appointment/Encounter القائمين، مع إبقاء هذا التنفيذ في نطاق synthetic/local proof ولم يُفتح إلى كتابة سريرية حية أو تكامل خارجي.

| المجال | ما نُفّذ | الدليل الحالي | الحد المتبقي |
|---|---|---|---|
| Laboratory Core | `CoreLabOrder` و`CoreLabOrderItem` و`CoreSpecimen` و`CoreSpecimenEvent`، من order إلى accession/collection/receive/process/analyze/validate، مع tenant scope وstate machine وIf-Match وidempotency وaudit | API tests و6 اختبارات Synthetic ناجحة؛ PostgreSQL fresh migration إلى 0013 ناجح | لا analyzer/LIS حقيقي، ولا multi-worker API load أو staging |
| Result Core | draft → technical validation → clinical validation → release؛ critical event يمنع release حتى acknowledgement؛ provenance وsource message replay؛ correction/amendment بإصدار جديد | critical/replay/safety API tests ناجحة | لا digital signature/MFA/fresh-session assurance، ولا notification provider خارجي |
| Clinical Access | patient grant محدود بالـpurpose/scope ومدة ≤72 ساعة، provider read، immediate revoke، expiry enforcement، access history وdeny-by-default | golden share/revoke وIDOR/permission paths ضمن الاختبار | لا provider directory display حقيقي، ولا break-glass governance أو staging audit review |
| Synthetic Backend | locks وreplay maps وbounded sharing وversioned revoke وaccess history، مع الحفاظ على backward-compatible fixture calls | `6 passed` | test-only؛ لا persistence أو multi-process guarantee |
| PostgreSQL | migration additive `20260828_0013`، FK/check/unique/index و21 permission seed guarded | fresh upgrade وschema gate وrollback/re-upgrade إلى `20260828_0013` ناجحة على DB disposable | لا تنفيذ على production/staging؛ compatibility drift يحتاج review مستقل |

الحزمة الجديدة لا تعيد استخدام public-token result sharing ولا legacy `order_service` ككاتب سريري. وهي تستخدم `AppointmentAuthorizationService` و`SyncCanonicalAuditService` وshared error envelope وopaque cross-metadata identifiers. كما تم توسيع Engineering Inventory ليكشف غياب authorization/audit/state/idempotency/version/concurrency/provenance/expiry/scope/history في هذه المجالات.

**حالة التحقق:** الاختبارات المركزة الخاصة بـLab/Result/Access هي `5 passed`، واختبارات Synthetic هي `6 passed`، واختبار PostgreSQL schema gate هو `1 passed`، مع استمرار regression Appointment/Encounter عند `14 passed`. أُعيد تشغيل full backend suite على الشجرة التي تحتوي Slice 03–05 ونجح بـ`2803 passed, 5 skipped, 165 warnings` خلال `313.59s`، exit code `0`. بقيت التحذيرات مصنفة كما هي ولم تُخفَ بمرشحات عامة.

أضيف أيضاً `backend/app/clinical/results/fhir.py` كـpure projection side-effect-free لـFHIR Observation؛ الاختبار يثبت version/provenance وإخفاء subject افتراضياً. لا ينفذ mapper أي publish أو اتصال خارجي.

تبقى بوابات `golden_path_passed=false` و`production_ready=false`. لا يُسمح بفتح frontend/mobile live writes أو نشر هذا المسار قبل إكمال transaction-failure proof، independent actor matrix، API concurrency، browser E2E، staging smoke، rollback rehearsal، remote CI readable، ومراجعة signing/MFA والسياسات التشغيلية.
