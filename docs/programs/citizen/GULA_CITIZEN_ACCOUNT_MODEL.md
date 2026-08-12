# GULA Citizen Account Model

حساب المواطن هو `niam_accounts` ضمن GULA Account الموحد، وليس patient record أو Health ID أو national identity أو organization membership أو role أو workspace. يحمل الحساب روابط الهوية والتحقق والملف والأجهزة والجلسات والموافقات والتفويضات والتدقيق، بينما تبقى السجلات السريرية في domain models المناسبة.

تحتفظ Wave 3 بنماذج `users` و`lab_users` وتربطها additive عبر `LegacyAccountLink`. تضيف C1 `CitizenRelationship` كطبقة علاقة صريحة بين account/legacy account وcitizen/patient. لا تُنشأ علاقة من phone أو national-ID matching تلقائياً، ولا تُنقل كلمات المرور أو tokens.

الحساب الواحد يستطيع امتلاك عدة workspaces، ويُعاد تقييم context والpermissions والentitlements عند كل switching. أي ambiguity أو missing verification أو revoked relationship يؤدي إلى fail closed.
