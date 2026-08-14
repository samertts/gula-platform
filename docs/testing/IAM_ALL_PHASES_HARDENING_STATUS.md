# IAM Phases 0–5 — Hardening and Test Status

## 1. النطاق

يوثق هذا المستند تغييرات hardening والاختبارات المنفذة على فرع `feat/iam-all-phases-test-hardening` فوق Phase 5. الهدف هو تحويل التوصيات إلى بوابات قابلة للتشغيل، مع إبقاء GULA هو النظام السريري المرجعي الوحيد وعدم إضافة أي provider حكومي أو مهني وهمي.

## 2. مصفوفة التغطية

| Phase | التغطية المضافة | دليل التشغيل الحالي | الحالة |
|---|---|---|---|
| 0 | مفردات audit الأمنية، uniqueness للقيم، deny-by-default في lifecycle | `test_foundation_phase0_phase1.py` | محسنة، لكن audit DB الكامل يحتاج integration |
| 1 | normalization، password policy، account lifecycle matrix | `test_foundation_phase0_phase1.py` و`test_account_lifecycle_phase1.py` | محسنة |
| 2 | refresh rotation، JTI blacklist، replay rejection، inactive-account rejection، rate-limit budget/headers | `test_auth_session_security_phase2.py` | محسنة، وتحتاج Redis multi-worker test |
| 3 | non-verified assurance = L0، method mapping، highest verified level، NotConnected boundary | `test_verification_hardening_phase3.py` | محسنة |
| 4 | organization/representative/ownership transition matrices، no auto-activation، provider boundary | `test_organization_hardening_phase4.py` | محسنة، وDB FK/IDOR يحتاج integration |
| 5 | Workspace service switch، context ownership، restricted denial، citizen idempotency، professional eligibility، HTTP actor/401/403/audit paths | `test_workspace_service_hardening_phase5.py` و`test_workspace_api_hardening_phase5.py` | محسنة، وlive PostgreSQL migration job منفصل |

## 3. نتائج الاختبارات المحلية

بعد الإضافات، نجحت suite الهوية في **116 اختباراً غير integration** مع اختبار واحد مستبعد عمداً بعلامة `integration`. نجحت اختبارات Frontend الخاصة بـWorkspace في **8 اختبارات**، شملت سبعة component/behavior tests واختبار axe accessibility واحداً، كما نجح `typecheck`.

نجحت security regression وtenant isolation في **66 اختباراً**. ظهرت ثلاثة تحذيرات غير حاجبة: تحذير حجم مفتاح test فقط، تحذير deprecated `datetime.utcnow()` في مولد contracts قديم، وتحذير دورة Foreign Key عند تنظيف SQLite test metadata.

## 4. إصلاحات startup وCI

أثناء تشغيل security regression ظهر blocker فعلي في startup: عدة FastAPI routes تعلن `204 No Content` دون `response_model=None`. تم تصحيح جميع decorators المتأثرة، ثم ظهر duplicate SQLAlchemy metadata لنماذج `niam_admin_branches`, `niam_admin_facilities`, و`niam_admin_departments`. تم توحيد هذه النماذج على `administrative_structure` مع إبقاء أسماء `PortalBranch`, `PortalFacility`, و`PortalDepartment` كaliases متوافقة للخدمات القديمة.

أضيف workflow مستقل باسم `iam-hardening.yml` يتضمن jobs منفصلة لـBackend identity، PostgreSQL migration، Frontend، وsecurity/tenant regression. كل job يرفع JUnit/log artifacts، وRuff في وضع read-only. يوجد validator محفوظ في `scripts/validate_iam_hardening_workflow.py` ويتحقق من jobs الأساسية ومسارات security regression.

## 5. حدود ما يثبته الاختبار

نجاح unit tests لا يثبت وحده أن migration طُبقت على قاعدة حية، أو أن provisioning المتزامن ينتج صفاً واحداً تحت PostgreSQL، أو أن audit chain محفوظ فعلياً بعد transaction commit. لذلك يبقى migration job PostgreSQL وrace test الحقيقيان بوابتين مستقلتين قبل إعلان Phase 5 مكتملة.

اختبارات Frontend تشغل `WorkspaceSelector` فعلياً وتتحقق من حالات loading، success، empty، error، demo، switch success، وswitch denial. لكنها لا تزال لا تثبت Playwright على بيئة API كاملة أو صلاحية session حقيقية من المتصفح.

## 6. سياسة الإغلاق

لا يجوز إنشاء tag من نوع `IAM-PHASE-*-COMPLETE` اعتماداً على هذا المستند وحده. الإغلاق يتطلب نجاح جميع jobs على GitHub، نجاح PostgreSQL upgrade/downgrade، نجاح race/uniqueness test، مراجعة بشرية، وعدم وجود integration أو mobile dimension غير موثقة.
