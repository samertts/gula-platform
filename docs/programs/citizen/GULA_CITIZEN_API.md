# GULA Citizen Workspace — API Contract

## مبادئ العقد

كل مسار citizen محمي بجلسة GULA، ويُحل الحساب والسياق من الخادم. لا يُعتبر `citizen_id` أو `patient_id` أو `user_id` أو `workspace` القادم من العميل دليلاً على الصلاحية. تستخدم الاستجابة أقل مجموعة حقول لازمة للغرض، مع pagination وprovenance وtimestamps UTC.

## مسارات own-context

| Method | Path | الغرض | جسم الاستجابة |
|---|---|---|---|
| GET | `/citizen-platform/me/dashboard` | ملخص المواطن الحالي | counts/actions فقط |
| GET | `/citizen-platform/me/profile` | account profile منفصل عن health profile | contact/preferences/verification summary |
| GET | `/citizen-platform/me/health-summary` | projection صحي مصرح | provenance وsource/status |
| GET | `/citizen-platform/me/appointments` | مواعيد السياق الحالي | appointment fields اللازمة فقط |
| GET | `/citizen-platform/me/lab-results` | النتائج النهائية المنشورة | `released` only، no preliminary values |
| GET | `/citizen-platform/me/radiology` | تقارير الأشعة المنشورة | report metadata أو temporary access فقط |
| GET | `/citizen-platform/me/medications` | أدوية/صرف مصرح | instructions/status، بلا تعديل prescription |
| GET | `/citizen-platform/me/notifications` | إشعارات الحساب | category/status/createdAt |
| GET | `/citizen-platform/me/consents` | الموافقات الفعالة | scope/version/purpose/status |
| GET | `/citizen-platform/me/access-history` | تاريخ الوصول الملائم للمواطن | actor/org/time/category/purpose |

تُضاف مسارات `/context/{context_id}/...` لاحقاً فقط بعد relationship/delegation resolver. لا تُضاف مسارات عامة تقبل `citizen_id` وتعيد data بلا policy.

## Compatibility paths

المسارات القديمة `/citizen-platform/{resource}/{citizen_id}` لا تُعامل كعقود citizen public. إما تُحجب افتراضياً، أو تُبقيها compatibility خلف dependency يثبت أن `citizen_id` داخل current relationship، مع audit للنجاح والرفض. لا يسمح compatibility path بتوسيع scope أو اختيار profile آخر من الواجهة.

## Authorization decision

```text
authenticate session
→ resolve account/person/identity
→ resolve workspace
→ resolve patient relationship/delegation/consent
→ check resource + purpose + state
→ query scoped projection
→ audit decision
→ return minimized response
```

## النتائج السريرية

لا تظهر للمواطن قيمة result قبل `released` أو الحالة المعتمدة التي يحددها domain policy. `entered`, `pending_review`, `approved` غير كافية وحدها لعرض قيمة سريرية كمعلومة نهائية. كل نتيجة منشورة تحمل source/status/occurredAt، ويُفصل critical notification عن presentation value.

## الأخطاء

تُستخدم `401` للجلسة المفقودة أو غير الصالحة، و`403` للسياق المصادق عليه لكن غير المصرح، و`404` عندما تفرض سياسة عدم كشف وجود المورد ذلك. لا تعاد exception traces أو national IDs أو raw tokens أو internal database identifiers غير اللازمة.

## التدقيق

كل access أو denial يسجل actor/account context، route، resource category، outcome، reason code، request ID، timestamp، مع عدم تسجيل PHI الخام. كل write حساس يسجل before/after وفق AuditService ويدعم idempotency/version checks.
