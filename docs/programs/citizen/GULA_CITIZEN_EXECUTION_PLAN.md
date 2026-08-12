# GULA Citizen Workspace — Execution Plan

## الهدف

تنفيذ Citizen Workspace داخل GULA الموحد على مراحل evidence-gated، بحيث تسبق الهوية والتفويض والخصوصية الواجهة والخدمات. الخطة لا تفترض وجود تكامل حكومي أو EMS أو PACS لم يثبت في المستودع.

## موجات التنفيذ

| الموجة | النطاق | مخرجات الإغلاق |
|---|---|---|
| C0 | Audit وGap Matrix | حالة repository، ownership، threat model، gap matrix معتمدة |
| C1 | Account + Person + Health ID relationship | schema additive، resolver، collision policy، rollback، no raw NID |
| C2 | Authentication + verification + recovery | contact verification، risk levels، MFA/step-up، session/device revocation |
| C3 | Authorization context | workspace resolver، patient relationship، guardian/delegation، consent checks، deny-by-default |
| C4 | Citizen API security | own-context endpoints، final-only projections، access audit، pagination، field minimization |
| C5 | Citizen application shell | frontend-v3 route، Arabic RTL، context indicator، progressive disclosure، Guide Assistant navigation-only |
| C6 | Profile/Security/Privacy | profile separation، security center، consent center، access history، legal pages |
| C7 | Health summary/timeline | provenance، status/source labels، clinical validation boundaries، no stale/current confusion |
| C8 | Appointments/queue/referrals | shared scheduling/patient-flow engines، idempotent writes، cancellation/retry |
| C9 | Laboratory/Radiology/Pharmacy | released results، secure reports/images، prescription read/refill contracts، no silent prescription mutation |
| C10 | Documents/Vaccination/Notifications/Tasks | expiring links، scoped sharing، critical notification rules، task/message separation |
| C11 | Family/Guardian/Delegation | explicit person context، scope/expiry/revocation، cross-context negative tests |
| C12 | Offline/synchronization | encrypted cache، ONLINE/OFFLINE/SYNCING/SYNC_ERROR، stale markers، conflict resolution |
| C13 | AI under governance | explicit AI label، approved sources، redaction، provenance، no diagnosis/prescription |
| C14 | Hardening/observability | IDOR tests، audit integrity، latency/error metrics، privacy-safe logs، rate limits |
| C15 | Accessibility/localization | Arabic-first RTL، English، keyboard/screen-reader/contrast/reduced-motion tests |
| C16 | Native/release certification | Android/iOS/Windows builds، secure storage، crash monitoring، rollback/DR evidence |
| C17 | E2E/release gate | 10 journeys، security/privacy/clinical/accessibility/offline/performance gates |

## C1 — أول دفعة تنفيذية

لا تبدأ C5 قبل تنفيذ العناصر التالية:

1. حماية جميع handlers في `backend/app/citizen_platform/routes.py` بجلسة GULA موثقة وrelationship resolver، مع رفض أي `citizen_id` لا يطابق السياق المسموح.
2. توفير own-context routes لا تحتاج إلى identifier يختاره العميل، مع إبقاء path-ID routes compatibility خلف policy مؤقتة ومراقبة.
3. تعريف final-only result projection وعدم إعادة preliminary/pending values إلى المواطن.
4. توثيق فشل access كـ403/404 حسب سياسة عدم كشف وجود المورد، مع audit record لا يحتوي PHI غير الضروري.
5. إضافة اختبارات cross-citizen، unauthenticated، expired/revoked relationship، result status، وfield minimization.

## C2 — التغييرات اللاحقة

بعد نجاح C1، يُنشأ relationship foundation additive بين NIAM person/account وnational citizen/patient. لا يُنشأ backfill تلقائي؛ تبدأ cohort اصطناعية أو read-only dry-run، ويُوقف rollout عند authorization divergence أو collision.

## بوابات كل موجة

لا تنتقل الموجة التالية إلا بعد نجاح unit/integration/API/authorization/security tests الخاصة بها. موجات الواجهة تحتاج production build وdirect-reload وRTL/accessibility evidence. موجات mobile تحتاج Android/iOS/Windows build evidence. موجات offline تحتاج stale/conflict/recovery evidence. موجة AI تحتاج provenance/redaction/audit evidence.

## سياسة الإيقاف والرجوع

يوقف التنفيذ عند أي cross-citizen leakage، authorization mismatch، missing audit event، preliminary result exposure، secret/PII leakage، أو migration incompatibility. الرجوع يكون عبر feature flag أو rollback migration، دون حذف البيانات أو الفروع أو تغيير deployment behavior.

## قرارات خارج التفويض الحالي

لا تشمل هذه الخطة اعتماد وسائل تحقق حكومية أو biometric integration أو live EMS أو production PACS أو store release ما لم يوجد connector معتمد واختبارات contract وأمن وخصوصية واعتماد تشغيلي مناسب.
