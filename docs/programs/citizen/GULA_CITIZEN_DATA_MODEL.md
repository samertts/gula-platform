# GULA Citizen Data Model

تفصل المنصة بين Account Profile وHealth Profile وPatient Record. `national_citizens` يحمل demographic/health identity reference، و`national_patients` يحمل clinical context ويرتبط بالمواطن عبر `citizen_id`. علاقة الحساب بالمواطن/المريض موجودة في `niam_citizen_relationships` ولا تُستنتج من client-selected IDs.

كل clinical projection يحمل source/provenance/status/occurredAt/lastUpdated، ويميز patient-reported عن clinician-recorded وعن system-derived. النتائج المعروضة للمواطن يجب أن تكون final/released وفق domain policy؛ لا يعاد preliminary أو pending value كأنه نتيجة نهائية.

لا تعاد السجلات كاملة إلى العميل. تستخدم DTOs purpose-specific وpagination وfield minimization وopaque identifiers. المستندات تستخدم expiring access links، والمشاركة تحدد resource/time/recipient/expiry/revocation، لا share-all افتراضياً.
