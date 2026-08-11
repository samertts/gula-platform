# Citizen Account and Role Model

Citizen Workspace يستخدم `niam_accounts` كحساب GULA الموحد. يمكن للحساب نفسه حمل citizen وprofessional workspaces، لكن كل workspace يحتاج assignment/entitlement وسياقاً مستقلاً. لا تنشأ حسابات منفصلة للمختبر أو المواطن إلا كـlegacy compatibility خارج المسار canonical.

الدور وحده لا يكفي للوصول إلى patient data. القرار النهائي يجمع account status، identity verification، workspace، organization/facility، permission، resource relationship، consent/delegation، والغرض من الوصول. أي غياب أو تعارض يؤدي إلى deny.

تبقى `users` و`lab_users` كما هي خلال Wave 3/C1، ويُربطان تدريجياً عبر mapping/relationship قابل للعكس. لا تُنسخ كلمات المرور أو refresh tokens إلى Citizen tables، ولا تُفعّل dual-write دون اعتماد وفحوص authorization divergence.
