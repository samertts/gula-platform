# GULA — Wave 3 Reversible Identity Mapping

**الحالة:** `DESIGNED — additive mapping only; no backfill or merge enabled`

**Base:** Alembic head `20260723_0002` على فرع main الحالي.

## الهدف

تثبيت طبقة ربط قابلة للعكس بين نماذج الحساب القديمة `users` و`lab_users` وبين نموذج NIAM الموجود: `niam_persons` → `niam_identities` → `niam_accounts`، مع إبقاء `organizations` و`facilities` و`niam_organizations` و`niam_assignments` ضمن حدودها الحالية. لا تُدمج الحسابات تلقائياً ولا تُنقل بيانات سرية خام إلى جدول الربط.

## mapping sources وtarget

| المصدر legacy | المفتاح | السياق | الهدف canonical | قواعد |
|---|---|---|---|---|
| `users` | integer `id` | `organization_id`, `facility_id`, `tenant_id`, `role`, `is_verified` | `niam_accounts.id` + identity/person | لا merge عند collision؛ تحقق email/phone/national hash عبر HMAC فقط |
| `lab_users` | integer `id` | `lab_id`, `role`, `province_id`, active | `niam_accounts.id` + `niam_assignments` | يبقى lab boundary فعالاً حتى اكتمال migration |
| `organizations` | integer `id`, stable `org_id` | org type/tenant/parent | `niam_organizations.id` أو mapping مؤسسي مستقل | لا تُفترض مطابقة ID بين النظامين |
| `facilities` | integer `id`, stable `facility_id` | organization | NIAM organization/facility context | تحقق parent organization قبل assignment |

## جدول الربط الإضافي

تضيف migration جدول `niam_legacy_account_links` بالحقول التالية: `source_kind` (`user`/`lab_user`)، `legacy_account_id`، `canonical_account_id` nullable، `source_fingerprint` HMAC لا يحتوي email أو national ID خاماً، `status` (`pending`, `validated`, `migrated`, `collision`, `rolled_back`, `blocked`)، `collision_reason`، `mapping_version`، `rollback_token`، وtimestamps. يفرض unique `(source_kind, legacy_account_id)` وforeign key canonical account، ويسجل index للحالة والبصمة.

الإضافة additive فقط. لا تتغير جداول users/lab_users ولا تُحذف بيانات ولا تُملأ mapping rows تلقائياً عند migration. يمنع service أي update بعد `migrated` إلا عبر transition صريح ومدقق.

## حالات التوافق

| الحالة | الفعل |
|---|---|
| `pending` | لا تغيير في auth؛ ينتظر dry-run والتحقق |
| `validated` | يسمح dual-read خلف feature flag ويقارن القرارين |
| `migrated` | canonical session/account هو المسار المفعّل للcohort، مع legacy rollback متاح |
| `collision` | يرفض الدمج، يسجل السبب، ويحتاج resolution يدوي موثق |
| `blocked` | يمنع الترحيل بسبب verification/tenant/safety constraint |
| `rolled_back` | يعيد cohort إلى legacy path دون حذف canonical evidence |

## rollout القابل للعكس

يبدأ التنفيذ بإضافة الجدول والنموذج والخدمة واختبارات transition فقط. بعد ذلك يشغل dry-run read-only على دفعات محدودة، وينتج collision report بلا PHI. لا يبدأ dual-write قبل مقارنة authorization server-side وsession behavior وaudit events. تُفعّل feature flag على organization/facility cohort، ويُراقب mismatch rate و401/403 وlogout/revocation وaudit integrity. عند أي mismatch أو safety signal، يُوقف flag ويُعاد cohort إلى legacy باستخدام `rollback_token`.

لا تُنقل refresh tokens أو كلمات المرور إلى المتصفح أو جدول الربط. تُنشأ جلسة جديدة من canonical account فقط بعد تحقق current session والـperm version، وتبقى cookie HttpOnly للويب وsecure storage للعملاء الأصليين.

## معايير الإغلاق

لا يُعلن اكتمال Wave 3 قبل وجود collision rate موثق، zero unexpected authorization divergence، اختبارات stale/conflicting role assignment، session rotation/revocation، organization/facility negative tests، audit before/after، fresh migration على SQLite وPostgreSQL، وrollback drill على cohort اصطناعي. أي اعتماد على IDs مختارة من الواجهة مرفوض.

## تنفيذ Wave 3 — حالة التحقق

تم تنفيذ طبقة mapping additive وقابلة للعكس عبر `LegacyAccountLink` و`LegacyMappingService`. تنشئ الخدمة رابطاً pending عند الطلب فقط، وتحسب `source_fingerprint` عبر HMAC، وتمنع الانتقالات غير المسموح بها، وتُسجل إنشاء الرابط والانتقالات عبر `AuditService` داخل نفس session. لا تنشئ حسابات canonical، ولا تنسخ كلمات مرور أو refresh tokens، ولا تنفذ backfill أو dual-write أو merge.

تم تحديث web legacy إلى cookie-only sessions: `frontend-v2` و`frontend/index.html` و`frontend/tiers.html` لا تقرأ أو تكتب JWT في localStorage، ويستخدم `frontend-v2` endpoint `/session` للتحقق من جلسة HttpOnly. تم أيضاً نقل مستهلك إحصاءات المختبر إلى `credentials: include` بدلاً من Bearer token قابل للقراءة في JavaScript.

تم تأمين `apps/gula-web-suite` عبر رفع tRPC إلى `11.18.0` المحلول من specifier `^11.8.0`، وتثبيت pnpm `10.34.4`، وتحديث lockfile مع overrides مصححة لـ `tar`, `fast-xml-parser`, `rollup`, `esbuild`, `lodash`, `lodash-es`, `path-to-regexp`, `picomatch`, وامتدادات transitive الأخرى. احتُفظ بـ wouter `3.7.1` حتى يبقى patch route-discovery الموروث فعالاً.

## أدلة الإغلاق المنفذة

| البوابة | النتيجة |
|---|---|
| `python3 -m compileall -q app migrations` | ناجحة |
| Fresh SQLite `alembic upgrade head` | ناجحة؛ `alembic current` = `20260811_0001 (head)` |
| Wave 3 + migration parser tests | `15 passed` |
| Backend full suite | `2293 passed`، مع تحذيرات deprecation غير حاجبة |
| gula-web-suite typecheck | ناجح |
| gula-web-suite Vitest | `15 passed` في 5 ملفات |
| gula-web-suite production build | ناجح؛ تحذيرات analytics env موجودة مسبقاً وليست build failures |
| `pnpm audit --audit-level=high` على lockfile المصحح | `No known vulnerabilities found` |

لا تزال عمليات تفعيل cohort أو dual-read/dual-write أو حذف/إعادة تسمية الفروع أو إصدار GitHub Release خارج هذه الموجة وتحتاج اعتماداً منفصلاً وفق HARD STOP.
