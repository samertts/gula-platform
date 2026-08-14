# IAM Phase 9 — Security, Immutable Audit, Governance & Compliance

## النطاق والقاعدة الحاكمة

تضيف Phase 9 طبقة security operations والتدقيق والحوكمة فوق NIAM Phases 0–8 دون إنشاء نظام هوية أو clinical record ثانٍ. يظل GULA هو مصدر القرار السريري والسياسة، بينما تكون أحداث الأمن والتدقيق append-only ومحدودة الوصول.

> **Fail closed:** فشل التحقق من صلاحية قارئ التدقيق، أو فشل سلامة السلسلة، أو غموض نطاق المنظمة لا يتحول إلى قراءة أو تصدير.

## قرار التوافق مع المصدر الحالي

يحتوي المصدر على `IdentityAuditEntry` في جدول `niam_audit_entries` وعلى `AuditService` يحسب `previous_hash` و`entry_hash`، كما يحتوي على legacy `AuditLog` و`audit_logs` وسلسلة قديمة ذات anchors. لن تُحذف السجلات القديمة أو تُعاد كتابتها. ستُوسّع `niam_audit_entries` بحقول event type/version/category/decision/reason/correlation/scope/classification، مع إبقاء `entry_hash` هو القيمة المخزنة لـ`event_hash` للتوافق.

ستحظر طبقة ORM تحديث أو حذف `IdentityAuditEntry`. تحقق السلسلة سيستخدم serialization canonical ثابتة وUTC server timestamps، ويُرجع `VALID` أو `INVALID` أو `INCOMPLETE` مع تشخيص غير سريري. لا يُدّعى أن جدولًا وحده يثبت immutability خارج حماية قاعدة البيانات والتخزين التشغيلي؛ لذلك يبقى anchor/HMAC الموجود legacy evidence منفصلًا عن canonical verification.

## Canonical AuditEvent mapping

| المتطلب | الحقل/السلوك في المصدر |
|---|---|
| event_id | `IdentityAuditEntry.id` |
| event_type | `event_type` |
| event_version | `event_version` |
| category | `category` |
| actor account | `actor_id` |
| actor identity | `actor_identity_id` |
| organization/facility/department/workspace | scope columns الجديدة |
| action/decision/reason | `action`, `decision`, `reason_code` |
| request/correlation | `request_id`, `correlation_id` |
| source/actor type | `source`, `actor_type` |
| previous/event hash | `previous_hash`, `entry_hash` as event hash |
| privacy | no token, OTP, password, private key, identity document, or clinical payload duplication |

## Audit access control and separation

تُضاف صلاحيات مستقلة: `audit.read`, `audit.read_sensitive`, `audit.export`, `audit.verify_integrity`, `security.incident.read`, و`security.incident.manage`. تُعطّل العلاقة القديمة التي منحت `audit.read` تلقائيًا لـ`organization_manager`، وتُنشأ أدوار catalog صريحة `audit_reviewer`, `security_administrator`, و`ministry_auditor` دون أي assignment تلقائي. `MINISTRY_AUDITOR` لا يُستنتج من البريد أو الاسم أو اختيار الواجهة.

قارئ التدقيق يقرأ فقط نطاق المنظمة الذي يثبته actor وmembership والـrole assignment. لا توجد update/delete endpoints. التصحيح الإداري، إن لزم مستقبلًا، سيكون event إضافيًا لا تعديلًا للسجل.

## Consent

تظل خدمة consent legacy مدعومة للاختبارات والعملاء الحاليين، لكن Phase 9 تضيف consent versioned على NIAM. كل تغيير في الشروط ينشئ version جديدة، ولا يُعاد استعمال السجل التاريخي. الحالة من `ACTIVE`, `WITHDRAWN`, `EXPIRED`, `REVOKED`. Grant/revoke/check يثبت actor من جلسة NIAM، ولا يقبل status أو actor أو granted_by من body. لا يحل consent محل authorization؛ يجب أن يمر الوصول الحساس أيضًا عبر AuthorizationDecisionService.

الفترات القانونية غير المعروفة لا تُخترع. يستمر حد 72 ساعة الموجود في legacy service كحد أمني تشغيلي مؤقت، ويُوسم أي retention/legal basis غير معروف بـ`LEGAL_REVIEW_REQUIRED`.

## Security incidents and alerts

تُضاف SecurityIncident بحالة انتقال صارمة: `OPEN → TRIAGED → CONTAINED → INVESTIGATING → RESOLVED → CLOSED`، مع فرع `FALSE_POSITIVE` من الحالات المفتوحة/المحققة فقط. لا يُنفذ automatic blocking بناءً على heuristic ضعيف. يعرض security dashboard مؤشرات محدودة ومجموعة أحداث عالية الخطورة؛ ويعتمد detection pipeline على DETECT/SCORE/CHALLENGE/BLOCK كسياسة مستقبلية، بينما التنفيذ الحالي يكتفي بالتجميع والتسجيل وعدم الحظر التلقائي.

## Export, retention, privacy, continuity

التصدير paginated ومحدود الحجم ومُسجل كحدث `DATA_EXPORT_REQUESTED`، ويعيد payload JSON مؤقتًا في الاستجابة دون public URL دائم. إعدادات الاحتفاظ تعرف data type وretention class وlegal basis وdeletion/archive strategy، لكن المدد القانونية المفقودة تبقى `LEGAL_REVIEW_REQUIRED`. لا تُحذف سجلات التدقيق المطلوبة للتحقيق. RPO/RTO لا تُخترع؛ تُوثق كـ`DECISION_REQUIRED` عند عدم وجود قرار تشغيلي معتمد.

## خارج النطاق

لا توجد موافقة حكومية أو تكامل وزارة صحة مُفترض، ولا ادعاء compliance قانوني عراقي. لا تُضاف cryptography مخصصة أو malware scanner مخترع. تُسجل هذه الفجوات كـ`PARTIAL` أو `LEGAL_REVIEW_REQUIRED` في تقرير التنفيذ.
