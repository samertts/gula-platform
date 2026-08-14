# IAM Memberships and Relationships

## الغرض

يمثل Membership علاقة قابلة للتدقيق بين حساب GULA ومنظمة في سياق محدد. لا يُعد Membership حساباً أو هوية أو منظمة أو Workspace أو Role أو Permission، ولا يمنح صلاحيات شاملة بذاته.

> **قاعدة القرار:** Membership + Role + Permission + Context = Authorization Decision. يظل القرار النهائي داخل Backend، بينما تستخدم الواجهات البيانات الفعالة للعرض فقط.

## النموذج

يحتوي `Membership` على account وidentity الاختياري، organization الإلزامية، وfacility/department/unit/workspace الاختيارية وفق `scope_type`. يحفظ النموذج `relationship_type`, `status`, `source`, timestamps، expiry، suspension/revocation reason، version، وmembership key idempotent.

يستخدم `MembershipInvitation` token hash فقط، ولا يحفظ raw token. الدعوة مرتبطة بالمنظمة والسياق، ويمكن أن تكون موجهة إلى account موثوق أو تبقى unresolved وفق السياسة. أما `MembershipApplication` فتمثل طلب الحساب لعلاقة مع منظمة، ولا تتحول إلى Membership active قبل مراجعة واعتماد actor مخول بالمنظمة.

## العلاقة مع Phase 5

يظل Workspace مستقلاً عن Membership. يمكن للعضوية أن تحمل workspace context، لكن eligibility والتبديل يظلان server-authoritative. لا تستطيع الواجهة إنشاء membership أو تعديل status أو scope، ولا يجوز لعضوية منظمة A أن تمنح وصولاً إلى منظمة B أو facility/department/workspace آخر.

## State machines

Membership transitions محصورة في `pending → active/rejected/revoked`، و`invited → active/rejected/revoked/expired`، و`active → suspended/expired/revoked/deactivated`، و`suspended → active/revoked/expired/deactivated`. لا يمكن إعادة تفعيل revoked أو rejected أو deactivated.

Application transitions محصورة في draft/submitted/under_review ثم approved أو rejected، مع cancel/expire من الحالات المسموح بها. Approval يتطلب ownership أو representative active في المنظمة؛ creation of application لا يؤدي إلى activation تلقائياً.

## Invitations

الدعوة cryptographically random، قصيرة العمر، single-use، revocable، ومحدودة بالـrecipient عند وجوده. يقارن الخادم hash token ولا يسجل السر. الفشل أو replay أو expiry يعيد خطأ مناسباً ولا يكشف membership أو account enumeration غير المصرح به.

## الأمن والتدقيق

يستخدم كل endpoint `get_current_niam_actor` لاستخراج account/session من access token وJTI والسجل الخادمي. لا تُقبل account_id أو actor_id أو status من body كمرجع ثقة. أحداث الإنشاء والتقديم والاعتماد والقبول والتعليق والإلغاء والدعوة تُحفظ عبر AuditService داخل hash chain، مع منع invitation secrets وcredentials من metadata.

## قاعدة البيانات

Migration `20260814_0004_membership_relationship_engine` تنشئ `niam_memberships`, `niam_membership_invitations`, و`niam_membership_applications` بــFKs إلى account/identity/organization/administrative hierarchy/workspace، وunique keys وindexes للحساب والمنظمة والسياق والحالة والانتهاء. history لا يُحذف عند revoke أو expire.

## حدود Phase 6

لا يضيف هذا التصميم Role Catalog أو Permission Catalog أو ABAC؛ هذه وظائف Phase 7 وPhase 8 بالترتيب. كما أن provider verification لا يحول تلقائياً إلى organization membership، ولا ownership relationship إلى platform administration.
