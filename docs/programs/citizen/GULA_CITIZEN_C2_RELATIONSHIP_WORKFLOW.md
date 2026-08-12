# GULA Citizen C2 — Relationship Administration Workflow

**الحالة:** Implemented and pushed on the Wave 3 review branch; no production relationship creation is performed.

**Implementation commit:** `3f716aea7ac6158418903ebab897d438a7cfb068`

**Remote branch:** `wave3-identity-dependency-hardening-20260811`

**Evidence:** C1/C2 targeted tests `12 passed`; Backend full suite `2305 passed, 251 warnings`; C2 migration fresh upgrade and downgrade/re-upgrade both passed.

## Contract

C2 يضيف admin-only endpoints تحت `/admin/citizen-relationships` لإنشاء علاقة `pending`، عرض العلاقات، تفعيل علاقة بعد verification reference، وإلغاء العلاقة بسبب reason code مضبوط. النسخة الأولى تدعم `legacy_user` مع `relationship_type=self` وpurpose `citizen_workspace` فقط. لا تدعم canonical account activation أو guardian/delegate أو legacy lab user حتى تُثبت عقودها.

## Safety rules

الإنشاء يتطلب `Idempotency-Key` بطول 16–128، ويحسب hash للمفتاح وrequest fingerprint. إعادة استخدام المفتاح مع نفس الطلب تعيد نفس العلاقة؛ إعادة استخدامه مع payload مختلف ترفض بـ409. يمنع scope wildcard، ويتحقق من أن المصدر User نشط ودوره citizen، وأن Citizen موجود وغير deceased/merged. patient_id اختياري لكنه إن أرسل يجب أن ينتمي إلى citizen نفسه ويكون active وغير merged.

التفعيل يتطلب ministry-level actor، علاقة pending، مصدر citizen active/verified، وverification reference غير حساس يُخزن digest له فقط. الإلغاء لا يقبل نصاً حراً؛ يستخدم reason codes مثل `user_request` و`verification_failed` و`security_event`. العمليات transaction-safe وتزيد version وتسجل action وactor وrelationship id والحالة السابقة/اللاحقة.

## Manual validation

يبدأ الاختبار في Demo/Test ببيانات اصطناعية فقط. أنشئ pending relationship بمفتاح فريد، تحقق من أنها لا تسمح بـ`/citizen-platform/me/*`، فعّلها بعد source verification، ثم تحقق من own-context. بعد ذلك أعد استخدام المفتاح، جرّب scope wildcard، مصدر غير موثق، patient من citizen آخر، علاقة منتهية/ملغاة، وسبب إلغاء غير مسموح. يجب أن تكون النتائج 409/403 المناسبة وأن يظهر audit decision/action.

لا يوجد endpoint عام للمواطن لإنشاء relationship، ولا يُسمح بإدخال SQL مباشر في production. أي cohort activation لاحق يحتاج review evidence وdry-run وموافقة منفصلة.
