# GULA Citizen Workspace — Gap Matrix

**التاريخ:** 2026-08-11

**النطاق:** تدقيق تطبيق المواطن داخل المنصة الموحدة، وليس إنشاء تطبيق أو نظام هوية منفصل.

**قاعدة القرار:** لا يُسمح ببدء واجهات Citizen Workspace الموسعة قبل تثبيت account context وHealth ID linkage وserver-side authorization. أي شاشة أو endpoint لا يثبت هذه الشروط يبقى `KEEP/FIX` أو `BLOCKED` ولا يُعلن جاهزاً للإنتاج.

## الحالة الحالية المؤكدة

المستودع يحتوي على أكثر من سطح للمواطن: `backend/app/citizen_platform/`، و`backend/app/routes/citizen_portal.py`، و`backend/app/national/`، وصفحة `frontend-v3/src/pages/citizen-platform/CitizenPlatformPage.tsx`. كما توجد واجهة `apps/gula-web-suite` تحتوي على patient timeline وسياق workspaces، لكنها ليست canonical web surface وفق قرارات Wave 2؛ لذلك تُستخدم كمرجع قابل لإعادة الاستخدام لا كهوية أو authorization بديل.

النماذج الوطنية الموجودة تفصل بين `national_citizens` و`national_patients`: للمواطن `health_number` ورابط national-ID محمي، وللمريض `citizen_id` وربط guardian محدود. نموذج NIAM يوفّر `niam_persons` و`niam_identities` و`niam_accounts` و`niam_assignments`، كما أن Wave 3 أضاف mapping قابلاً للعكس للحسابات legacy. لا يوجد بعد رابط معتمد ومثبت بين GULA Account وCitizen/Patient relationship يستطيع citizen-platform استخدامه دون fallback إلى phone أو national-ID matching.

## المصفوفة

| Current | Target | Gap | Risk | Dependency | Action | Validation |
|---|---|---|---|---|---|---|
| `Citizen` يملك `health_number` متسلسلاً وحقولاً للحالة والهوية، و`Patient` يكرر `health_number` ويرتبط بـ`citizen_id`. | Health ID ثابت ومُدار مركزياً، opaque في الواجهات، منفصل عن national ID وعن patient record. | لا يوجد canonical Health ID relationship مع NIAM account/person، ولا policy واضحة لاستخدام public identifier. | كشف معرفات صحية أو ربط خاطئ بين شخصين. | NIAM person/identity/account، MPI، patient linkage. | تصميم Health ID reference additive ومشفّر/opaque، ثم تنفيذ mapping بعد اعتماد ownership وcollision policy. | Unit/integration tests للـcollision، non-disclosure، وlink/unlink audit. |
| Wave 3 يملك `LegacyAccountLink` بين users/lab_users وNIAM account. | Citizen account يستخدم GULA Account نفسه مع citizen workspace، دون citizen-only auth stack. | لا توجد علاقة account → person → citizen/patient relationship في مسار المواطن. | duplicate identity، takeover، أو فشل في workspace switching. | Wave 3 mapping، NIAM assignments، verification states. | إضافة relationship foundation منفصلة عن account وpatient، دون backfill أو dual-write تلقائي. | Fresh migration، rollback، authorization context tests. |
| `/citizen-platform/*/{citizen_id}` يمرر caller-supplied `citizen_id` إلى SDK ولا يعتمد على `get_current_user`. | كل resource access يُشتق من authenticated account/context أو delegation موثق؛ لا يُسمح بالاعتماد على ID من العميل. | سطح IDOR محتمل وعرض بيانات غير مصادق عليه. | كشف سجلات صحية لمواطن آخر، وهو خطر حرج. | Account-to-citizen resolver، delegation/guardian policy، audit service. | إيقاف المسارات غير المحمية، إضافة auth/context guard، وجعل own-record endpoints لا تحتاج citizen ID من العميل. | 401/403 negative tests، cross-citizen tests، audit-denial tests. |
| `/citizen/*` legacy portal يربط patient rows عبر phone أو `national_id_hash`. | Patient relationships صريحة، versioned، scoped، قابلة للإلغاء والتدقيق. | matching غير canonical ولا يدعم guardian/delegate scope بدقة. | collision أو تسريب records عند تشارك phone/تغيير البيانات. | MPI، consent، delegation، identity verification. | إبقاء legacy read path مؤقتاً خلف compatibility policy، ثم تصميم migration read-only إلى canonical relationship. | collision fixtures، revoked/expired relationship tests، no raw NID logs. |
| `frontend-v3` يعرض `citizen-platform` خلف `adminRoles`، ويستدعي endpoints بلا `citizen_id` رغم أن backend يطلبه. | Citizen Workspace reachable for citizen account داخل نفس shell، مع role/context-based nav. | route mismatch وواجهة admin placeholder وليست citizen experience. | شاشة لا تعمل أو fallback يدفع المطورين إلى bypass authorization. | Backend citizen contracts، account context، localization/accessibility. | بعد تثبيت backend contract، تحويل route إلى role/context workspace page typed، وإزالة generic DataTable placeholder. | Production build، direct reload، RTL/a11y، API contract tests. |
| `apps/gula-web-suite` يملك patient timeline scoped عبر `linkedUserId`، لكنه stack منفصل ذو users/roles مختلفة. | محرك واحد للصلاحيات والهوية؛ لا duplicate auth/account. | احتمال انقسام authorization إذا استُخدم كمسار citizen مستقل. | divergence بين web surfaces ومصادر البيانات. | frontend-v3 canonical decision، backend API gateway. | استخدم patterns فقط، ولا تنقل account/identity logic إليه. | architecture review وrepository grep يمنع duplicate identity. |
| timeline الحالي يضم نتائج testResults مع statuses متعددة ويعرض value/diagnosis/notes مباشرة. | المواطن يرى النتائج النهائية المصرح بها مع provenance وstatus واضح، ولا يرى preliminary كأنه final. | لا يوجد final-only contract موحد في كل citizen surfaces، والـdata minimization غير مكتملة. | ضرر سريري أو كشف بيانات غير مؤكدة. | result state machine، release policy، audit. | تعريف released/final projection purpose-specific، مع إخفاء fields غير اللازمة. | tests لـentered/pending/approved/released/rejected وfield minimization. |
| توجد services للappointments, lab, radiology, pharmacy, notifications, consent, offline وprivacy داخل `citizen_platform`. | الخدمات موحدة ومتكاملة مع shared engines وauthorization وoutbox. | كثير منها SDK facades دون إثبات API/database/production integration في المسار نفسه. | claims تشغيلية غير صحيحة أو بيانات mock/in-memory. | service capability registry، integration hub، observability. | تدقيق كل service إلى KEEP/FIX/HARDEN/MIGRATE، وعدم عرض capability غير مثبتة. | contract/integration tests وhealth/readiness evidence. |
| يوجد GuideAssistant في `frontend-v3`. | مساعد واضح أنه AI، لا يشخّص ولا يصف ولا يتجاوز clinician، ويستخدم مصادر معتمدة عند المعلومات السريرية. | لا يوجد بعد citizen-specific policy/provenance contract ظاهر في هذا التدقيق. | hallucination أو خلط الإرشاد العام بتشخيص. | AI governance، approved sources، privacy redaction. | إبقاء المساعد navigation-first في Citizen Wave الأولى، وتأجيل clinical explanation إلى AI governance phase. | prompt/data-boundary tests، audit، redaction tests. |
| Android/desktop موجودان وWave 3 أشار إلى secure storage، لكن release builds وoffline synchronization غير مثبتين هنا. | Web/Android/Windows يعملون على العقود نفسها، مع encrypted offline state وsync status. | لا توجد شهادة native/release/offline لهذه الموجة. | stale data أو اختلاف authorization بين المنصات. | shared API contracts، device/session security، sync engine. | تأجيل release/store work حتى API/security gates؛ تنفيذ contract tests أولاً. | Android/Windows build gates، offline stale/conflict tests. |
| Demo mode موجود على مستوى المنصة العامة. | Citizen Demo مع synthetic data وعزل كامل عن production DB/Redis/secrets/connectors. | لم يُثبت بعد citizen-specific demo seed أو cross-environment isolation لهذا السطح. | تسريب بيانات حقيقية أو استخدام demo كمسار bypass. | startup guard، environment separation، seed/reset. | إضافة demo acceptance tests قبل أي public citizen preview. | DB/Redis endpoint isolation، synthetic-data assertions، expiry/read-only tests. |

## الأولويات

| الأولوية | النطاق | القرار |
|---|---|---|
| P0 | حماية `/citizen-platform` ومنع caller-supplied IDOR | تنفيذ قبل أي citizen UI أو public demo. |
| P0 | account/person/citizen/patient relationship contract | تصميم additive ومتوافق مع Wave 3؛ لا backfill تلقائي. |
| P1 | final-only health projections وdata minimization | تنفيذ قبل عرض results/timeline. |
| P1 | canonical frontend-v3 Citizen Workspace route | بعد ثبات P0 backend contract. |
| P1 | guardian/delegation/consent/access history | يعتمد على relationship foundation وpolicy engine. |
| P2 | appointments, queue, radiology, pharmacy, documents, vaccination | تباعاً بعد shared contracts والتكاملات المثبتة. |
| P2 | offline, native builds, AI clinical capabilities | لا تُعلن جاهزة قبل release/security gates. |

## حدود هذه الموجة

لا تتضمن هذه المصفوفة دمج User وLabUser، ولا حذف citizen portal، ولا إعادة تسمية frontend-v3، ولا backfill، ولا dual-write، ولا store release، ولا تغيير deployment behavior. كل هذه الأعمال تحتاج ADR واعتماداً منفصلاً مع rollback evidence.
