# Command 06 — تقرير معالجة عوائق SAFE_STOP المتبقية

**المشروع:** GULA Platform
**النطاق:** identity parity، logout/session boundary، CSRF/CORS، NIAM pilot، والاختبارات
**الفرع:** `security/p0-bootstrap-alembic`
**المرجع:** Command 05 commit `4bd9c3a4`
**رأس Alembic:** `20260815_0025` — رأس واحد
**التاريخ:** 2026-08-16
**القرار:** `AUTHENTICATION_RUNTIME_PARTIAL` مع بقاء `SAFE_STOP` للتفعيل التشغيلي

## الملخص التنفيذي

تمت معالجة العوائق التي يمكن إصلاحها وإثباتها داخل المستودع والبيئة المحلية دون فتح production أو استخدام تكامل حكومي أو الادعاء بوجود staging حقيقي. شملت المعالجة إضافة عقد parity read-only بين الحساب legacy والحساب canonical، وتثبيت فصل current-session logout عن all-sessions logout في طبقة NIAM، وإضافة اختبار صريح يمنع أي CSRF test bypass من التسرب إلى production، ثم إعادة تشغيل البوابات المحلية الكاملة.

لا يقوم عقد parity بإنشاء حساب أو نسخ كلمة مرور أو هاتف أو بريد أو national ID أو منح صلاحية. النتيجة `ready_for_review` تعني أن الربط يمكن عرضه للمراجعة البشرية فقط؛ ولا تعني الموافقة على migration أو single-write cutover.

> بقيت متطلبات PostgreSQL وRedis staging الحقيقي وTLS/ACL ومدير الأسرار وAndroid/Flutter خارج نطاق الإثبات المحلي. لذلك لم يُرفع قرار SAFE_STOP ولم يتم push أو merge أو deployment أو production migration.

## الإصلاحات المنفذة

### عقد identity parity read-only

أضيف `backend/app/identity/services/identity_parity_service.py`. يقارن العقد فقط بين حالة link، وcanonical account identifier، وحالة النشاط، وحالة Account، وتطابق الدور عبر mapping صريح اختياري. لا يعيد العقد أي PII أو credential، ولا يكتب قاعدة البيانات، ولا يغير authorization decision.

تُحجب النتيجة عند عدم اكتمال أي من الشروط التالية: link ليس `migrated`، canonical identifier مختلف، الحساب legacy غير فعال، الحساب canonical غير فعال أو ليس `active`، أو الدور لا يطابق mapping المعلن. هذا يحول غياب mapping أو وجود collision إلى حالة مراجعة/رفض بدلاً من fallback امتيازي.

### فصل logout scopes

أضيف method صريح `logout_current_session` في `AuthenticationService`، وأصبح `logout` alias توافقياً لا يدل إلا على current-session logout. تستخدم NIAM auth وSessions API method الصريح، بينما يبقى `logout_all_sessions` منفصلاً ويعمل على جلسات الحساب المملوكة فقط.

أضيف إلى audit metadata حدّ authorization واضح: `owned_session` للإنهاء الحالي و`owned_account` لإنهاء جميع الجلسات. بقيت أسماء audit الأساسية متوافقة مع العقد السابق، ولم تُستخدم legacy `perm_version` كبديل صامت عن NIAM session revocation.

### CSRF/CORS production boundary

أضيف اختبار يثبت أن وجود `ENV=production` لا يفعّل bypass الاختبارات: إذا كانت جلسة جديدة تحمل CSRF cookie ولم ترسل header المطابق، يُرفض الطلب حتى مع Origin مسموح. يبقى bypass TestClient محصوراً بـ`ENV=test` داخل middleware ولا ينطبق على staging أو production.

### اختبارات parity وboundary

أضيفت ثلاثة اختبارات parity للحالات السليمة، وغير المرحّلة، والمتعارضة/غير الفعالة. كما أُعيد تشغيل اختبارات auth/session وclinical gateway وCSRF، مع الحفاظ على قاعدة أن غياب mapping يمنع القراءة قبل الوصول إلى السجل السريري، وأن الردود لا تسرب حقول legacy الحساسة.

## نتائج البوابات

| البوابة | النتيجة |
|---|---:|
| Backend non-integration الكامل | **2649 passed**, 42 deselected |
| Backend integration مع SQLite migration وRedis محلي مشترك | **41 passed**, 1 skipped |
| اختبارات المعالجة المستهدفة | **23 passed** قبل التوسعة النهائية، ثم 14 اختباراً مستهدفاً بعد إضافة production CSRF test |
| Frontend Vitest | **51 passed** ضمن 15 test files |
| Frontend typecheck | ناجح |
| Frontend build | ناجح |
| Ruff على الملفات المعدلة | ناجح |
| Python compileall | ناجح |
| `git diff --check` | ناجح |
| Alembic head | رأس واحد: `20260815_0025` |

كان فشل بوابة Ruff الأول ناتجاً عن مسار أمر غير صحيح بعد الدخول إلى مجلد `backend`، وليس عن خطأ source. بعد تشغيل المسارات من جذر المستودع ثم إصلاح import `Mapping` إلى `collections.abc` نجحت البوابة بالكامل.

## حالة العوائق بعد المعالجة

| العائق | الحالة الحالية | سبب عدم إعلان الاكتمال |
|---|---|---|
| identity parity المحلي | **معالج محلياً** | يلزم operator review وبيانات staging قبل أي migration |
| current/all logout boundary | **معالج محلياً** | يلزم HTTP race test على PostgreSQL/Redis staging |
| CSRF test bypass leakage | **معالج ومختبر** | يلزم browser test على origins الفعلية |
| AsyncSession runtime | **معالج محلياً** | لم يُثبت عبر PostgreSQL deployment حقيقي |
| Redis shared/fail-closed | **معالج ومختبر محلياً** | لا يوجد Redis staging TLS/ACL أو multi-worker deployment فعلي |
| legacy/NIAM single-write migration | **محجوب عمداً** | يحتاج parity cohort ومراجعة بشرية وخطة rollback |
| Android/Flutter parity | **محجوب بيئياً** | SDKs غير متاحة في البيئة الحالية |

## القيود وقواعد SAFE_STOP

لا يجوز إنشاء canonical account أو نسخ credentials أو تفعيل dual-write استناداً إلى نتيجة parity فقط. ولا يجوز جعل Frontend membership أو role مصدراً لقرار authorization. يبقى القرار server-authoritative عبر NiamActor وWorkspace Context والروابط المراجعة.

إذا فشل Redis fail-closed أو tenant isolation أو refresh replay serialization في staging، يجب التوقف فوراً وعدم الانتقال إلى single-write أو production. لا يُعتبر local SQLite migration أو Redis loopback بديلاً عن PostgreSQL وRedis staging الحقيقيين.

## القرار النهائي

تم إصلاح العوائق البرمجية المحلية التي يمكن معالجتها دون اعتماد خارجي، مع نجاح بوابات الاختبار. القرار يبقى `AUTHENTICATION_RUNTIME_PARTIAL` مع `SAFE_STOP` قبل التفعيل التشغيلي، لأن الإثبات المتبقي يتطلب PostgreSQL وRedis staging معزولين، TLS/ACL، secrets manager، browser security testing فعلياً، ومصفوفة parity معتمدة، إضافة إلى Android/Flutter SDKs.

لا توجد تغييرات إنتاجية، ولا push أو merge أو deployment أو production migration. الخطوة التالية الآمنة هي تشغيل نفس العقود في staging مع بيانات اصطناعية أو نسخة معزولة، ثم إصدار قرار جديد فقط بعد مراجعة بشرية لسجلات parity والعزل.
