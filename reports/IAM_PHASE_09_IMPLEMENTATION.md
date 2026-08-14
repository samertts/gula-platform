# تقرير تنفيذ IAM Phase 9 — الأمن، التدقيق غير القابل للتغيير، الحوكمة والعزل

**المشروع:** GULA Platform
**المستودع:** `samertts/gula-platform`
**الفرع:** `feat/iam-phase9-security-audit`
**خط الأساس:** `feat/iam-phase8-authorization-engine`
**التاريخ:** 2026-08-14
**المنفذ:** Manus AI
**الحالة:** جاهز للمراجعة البشرية بعد إتمام الفحوص المحلية؛ لم يتم الدمج أو النشر تلقائيًا.

## الملخص التنفيذي

تم تنفيذ Phase 9 فوق المصدر الفعلي لمراحل IAM السابقة، مع إبقاء GULA **النظام السريري الوحيد لحفظ السجل** ونقطة فرض سياسات الوصول. أضيفت طبقة canonical audit ذات سلسلة تجزئة SHA-256، وإدارة موافقات NIAM بإصدارات وسجل append-only، وإدارة حوادث أمنية ذات آلة حالات صريحة، كما تم تشديد مسارات الإدارة والامتثال وربطها بمحرك القرار المركزي في Phase 8.

لا تنشئ هذه المرحلة نظام حسابات أو قاعدة بيانات ثانية، ولا تمنح أي خدمة متخصصة صلاحية اعتماد النتائج السريرية. وتظل الاتصالات العابرة للمستودعات خاضعة لعقود الأحداث versioned/idempotent الموجودة في بنية المنصة؛ Phase 9 لا يضيف تكاملات حكومية أو تكاملات مزودين غير مثبتة.

> **المبدأ الأمني:** كل قرار مصادقة وتفويض وامتثال هو قرار خادمي fail-closed. لا تُعد الواجهة الأمامية أو أي قيمة واردة من client body مصدرًا موثوقًا لحالة العضوية أو الحساب أو actor أو workspace.

## ما تم تنفيذه

| المجال | التنفيذ الفعلي |
|---|---|
| Canonical audit | توسيع `IdentityAuditEntry` بإصدار الحدث، التصنيف، actor، facility/department/workspace، القرار، reason code، request/correlation IDs، source، وdata classification. |
| Hash chain | إضافة `CanonicalAuditService` بسلسلة SHA-256، ربط كل إدخال بالـhash السابق، append-only semantics، redaction للمفاتيح السرية، البحث، والتحقق بحالات `VALID` و`INVALID` و`INCOMPLETE`. |
| Audit API | إضافة `GET /niam/audit` للبحث، `GET /niam/audit/export` للتصدير غير الدائم، و`GET /niam/audit/integrity` للتحقق؛ جميعها تمر عبر Phase 8 authorization. |
| Consent | إضافة `NiamConsent` و`NiamConsentService` لسجل موافقات versioned وappend-only، مع حالات grant/withdraw/expire، actor server-authoritative، وحد أقصى 72 ساعة ضمن النموذج الحالي. |
| Consent API | إضافة grant/list/check/withdraw عبر مسارات `/niam/consents`، مع منع client من تحديد actor أو هوية الحساب بشكل authoritative. |
| Security incidents | إضافة `SecurityIncident` مع severity/status وآلة حالات صريحة: `OPEN → TRIAGED → CONTAINED → INVESTIGATING → RESOLVED → CLOSED/FALSE_POSITIVE`، وحماية version guard لمنع الكتابة المتعارضة. |
| Security API | إضافة list/create/update/dashboard ضمن `/niam/security`، مع المصادقة والتفويض المركزيين وسجل التدقيق للأحداث الأمنية. |
| Admin hardening | إعادة تشديد مسارات الإدارة: `NiamActor`، تفويض Phase 8، فحص parent-resource IDOR للـportal/branch/facility، actor server-authoritative، canonical audit لكل mutation، وعدم قبول `credentials_encrypted` من client. |
| FHIR SSRF | التحقق من `base_url` عبر HTTPS فقط، منع embedded credentials وlocalhost وmetadata endpoint والعناوين الخاصة والمحلية، واشتراط `FHIR_ALLOWED_HOSTS` allowlist. |
| Compliance hardening | إضافة `organization_id` إلى `ComplianceCheck`، وتطبيق tenant filtering على القراءة والتشغيل والتقرير والحالة، وتثبيت `checked_by` و`generated_by` من actor الخادمي. |
| Route guard | إضافة auth dependency عامة إلى subrouters الحساسة: governance، trust، lifecycle، federation، certificates، workflows، notifications، adaptive auth، admin، وcompliance، مع الإبقاء على authorization التفصيلي داخل المسارات التي تتطلبه. |
| Catalog governance | migration تضيف خمسة أدوار محددة واثنتي عشرة صلاحية لازمة لهذه المرحلة، وتزيل overgrant `audit.read` من `organization_manager`. لم تتم إضافة صلاحيات سريرية أو صلاحيات تخمينية لمسارات غير موجودة. |
| Migration | `20260814_0006_security_audit_governance.py` ينشئ جداول consent/incidents، يضيف أعمدة canonical audit، يضيف tenant key للامتثال، ويحتوي downgrade قابلًا للعكس. |
| Tests وCI | إضافة اختبارات Phase 9 للوحدة واختبار PostgreSQL migration/schema، وربط اختبار migration ببوابة `iam-hardening.yml`. |

## الإصلاحات الأمنية المهمة

### منع IDOR والعزل التنظيمي

تتحقق مسارات الإدارة من parent resource من قاعدة البيانات قبل إنشاء child resource، ثم تقارن `organization_id` المرسل مع القيمة الخادمية. لا يمكن للطلب إنشاء branch تحت portal من مؤسسة أخرى أو facility تحت branch خارج tenant. وتُستخدم organization filters في مسارات الامتثال والبحث والتقارير بدل الاعتماد على معرفات client وحدها.

### منع mass assignment وتسريب الأسرار

أزيلت إمكانية تمرير `credentials_encrypted` من مدخلات العميل، وتُعاد payloads الخاصة باتصالات FHIR دون الحقل المشفر. كما لا تسجل canonical audit metadata أسرارًا معروفة مثل token/password/secret/key، ولا تنشئ endpoints التصدير روابط عامة دائمة.

### actor server-authoritative

لا تعتمد mutations في admin/compliance/consent/security على `actor_id` أو `checked_by` أو `generated_by` القادم من body. مصدر actor هو `NiamActor` الناتج من JWT وJTI وactive session ثم يُمرر للخدمات صراحة. وفي admin portal أُصلح خلل كان يستخدم `portal.id` قبل إنشاء portal؛ أصبح الاستدعاء يمرر `created_by=actor.account.id`.

### منع SSRF

لا يُسمح باتصال FHIR إلا إلى HTTPS host موجود في `FHIR_ALLOWED_HOSTS`. تُرفض العناوين الخاصة والـloopback والـlink-local وmetadata endpoints، كما تُمنع credentials المضمنة في URL. يجب ضبط allowlist في بيئة الإنتاج؛ عدم ضبطها يؤدي إلى رفض hosts غير المعروفة، ولا يمثل ذلك اعتمادًا تلقائيًا على أي مزود.

## بوابات الجودة والنتائج الفعلية

| البوابة | النتيجة الفعلية |
|---|---|
| Ruff على `app/identity` | **PASS — All checks passed** |
| Python `compileall` على identity | **PASS** |
| Backend identity regression غير التكاملية | **162 passed, 3 deselected** من أصل 165 collected |
| Phase 9 unit tests | **10 passed** ضمن regression |
| PostgreSQL migration test | موجود ومربوط في CI، وموسوم integration؛ لم يُشغّل محليًا لعدم توفر PostgreSQL integration fixture |
| NIAM route import/discovery | **PASS — 205 routes**، مع `/niam/health` و`/niam/audit` و`/niam/security/incidents` |
| Frontend tests | **PASS** — `npm run test -- --run` خرج بنجاح |
| Frontend typecheck | **PASS** |
| Frontend production build | **PASS** — Vite/PWA build اكتمل بنجاح |
| Flutter/Dart | غير متاح في sandbox؛ لا توجد تعديلات mobile في Phase 9، ويجب تشغيل analyzer/formatter في بيئة Flutter أو CI |

## ملفات التنفيذ الرئيسية

| الملف | الغرض |
|---|---|
| `backend/app/identity/services/canonical_audit.py` | canonical hash-chained audit، redaction، search، integrity verification |
| `backend/app/identity/models/audit.py` | أعمدة وأحداث audit الجديدة |
| `backend/app/identity/models/consent.py` | نموذج الموافقة النسخية append-only |
| `backend/app/identity/services/consent_service_v2.py` | دورة حياة الموافقة والتحقق من المدة والفاعل |
| `backend/app/identity/models/security.py` | نموذج الحوادث وenums الخاصة بها |
| `backend/app/identity/services/incident_service.py` | آلة حالات الحوادث وversion guard |
| `backend/app/identity/api/audit.py` | البحث والتصدير والتحقق من audit |
| `backend/app/identity/api/consents.py` | grant/list/check/withdraw للموافقات |
| `backend/app/identity/api/security.py` | إدارة الحوادث ولوحة الأمن |
| `backend/app/identity/admin/routes.py` | مسارات الإدارة المحمية مع IDOR وactor hardening |
| `backend/app/identity/admin/services.py` | admin mutations وSSRF validation وcanonical audit |
| `backend/app/identity/compliance/routes.py` | مسارات الامتثال المحمية والمعزولة تنظيميًا |
| `backend/app/identity/compliance/services.py` | tenant-filtered checks/reports وcanonical audit |
| `backend/migrations/versions/20260814_0006_security_audit_governance.py` | مخطط Phase 9 وcatalog seeds وdowngrade |
| `backend/tests/identity/test_security_audit_phase9.py` | اختبارات hash chain/redaction/consent/incidents/route hardening |
| `backend/tests/identity/test_security_audit_migration_phase9.py` | اختبار PostgreSQL للـschema/catalog/overgrant removal |
| `docs/architecture/IAM_PHASE_09_SECURITY_AUDIT_GOVERNANCE.md` | وثيقة التصميم المعمارية |

## حدود مقصودة وعدم ادعاءات زائفة

لا يدعي هذا التنفيذ تحقيق امتثال قانوني أو موافقة من وزارة الصحة العراقية أو أي جهة حكومية. وجود controls تقنية لا يساوي compliance certification. فترات الاحتفاظ القانونية، سياسات المراجعة البشرية، ومتطلبات jurisdiction-specific تحتاج **LEGAL_REVIEW_REQUIRED** قبل اعتمادها.

لم تُخترع قيم RPO/RTO؛ الحالة **DECISION_REQUIRED**. ولم تُنشأ مراقبة شخصية أو حظر تلقائي قائم على heuristics ضعيفة. كما لم تُنفذ Phase 10 الخاصة بـABAC/contextual authorization، ولم تُنشأ صلاحيات أو integrations لا يقابلها functionality موثقة.

تظل الموافقات والحوادث والتدقيق أدوات governance داخل NIAM، لكنها لا تمنح أي خدمة متخصصة صلاحية اعتماد نتيجة سريرية أو تغيير GULA كسجل سريري. ولا يحدث organization activation تلقائي، ولا توجد duplicate user/account systems.

## القرار والحالة التالية

Phase 9 **ناجح محليًا على مستوى المصدر والاختبارات المذكورة أعلاه**، مع اختبار migration PostgreSQL محفوظ لبوابة CI. الخطوة التالية التشغيلية هي staging commits صريحة، push للفرع، ثم إنشاء PR مستقل فوق `feat/iam-phase8-authorization-engine` ومراقبة بوابات GitHub Actions. لا يوجد merge أو deployment تلقائي، ولا ينبغي وضع completion tag قبل نجاح البوابات البعيدة ومراجعة بشرية صريحة.

**حالة PR:** ستُملأ بعد push وإنشاء Pull Request.
**حالة CI البعيدة:** ستُسجل بعد إنشاء PR؛ أي فشل Vercel بسبب rate limit خارجي سيُفصل عن نتائج كود Phase 9.
