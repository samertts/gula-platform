# Slice 12 — النواة المالية والتأمين

## نطاق التنفيذ

أضيفت نماذج ومسارات canonical تحت namespace `core_financial_*` مع إبقاء نماذج وجداول Finance legacy كما هي دون overwrite أو حذف أو dual-write صامت. تستخدم المبالغ integer minor units فقط، وتحتوي الفاتورة على قيد قاعدة بيانات يثبت معادلة الإجمالي الصافي.

تتطلب الكتابات المالية سياق NIAM وworkspace وorganization/facility وobject authorization. ترتبط الفاتورة اختيارياً بتغطية canonical بعد التحقق من member/patient وorganization، ولا تُقبل مطالبة payer لا يطابق تغطية الفاتورة. أضيفت idempotency receipts وrow locks وIf-Match وaudit ضمن المعاملة.

## المزوّدات الخارجية

لا يوجد اتصال فعلي بتأمين أو دفع. نتيجة eligibility غير الموثقة تبقى `UNKNOWN`، وحالة الدفع عند عدم توفر المزوّد تبقى `PENDING`. لا يقبل capture قيمة client-controlled مثل `signature_valid=true`؛ التحقق محصور في synthetic server-side event verifier وبنافذة زمنية وnonce فريد.

## أدلة قابلة لإعادة التشغيل

| الدليل | النتيجة |
|---|---|
| `tests/test_financial_core_api.py` | 3 اختبارات ناجحة، تشمل namespace، IDOR، signature proof، SoD، replay، ledger/refund guards |
| PostgreSQL 16 disposable | `alembic upgrade head` وصل إلى `20260828_0019` |
| rollback | `alembic downgrade 20260828_0018` ثم upgrade إلى head نجح |
| schema gate | جداول `core_financial_*` و`coverage_id` وnonce uniqueness وbill total check موجودة |
| quality | Ruff للملفات المعدلة وcompileall و`git diff --check` ناجحة |

## الحدود المتبقية

لا تمثل هذه الأدلة تكاملاً مع provider حقيقي، ولا تثبت staging أو remote CI أو full-suite بعد التغييرات الحالية. لذلك تبقى الجاهزية `production_ready=false`، وتبقى settlement/reconciliation الخارجية غير مكتملة تشغيلياً.

> قاعدة السلامة: لا تُوقف الرعاية الطارئة بسبب فشل التأمين أو الدفع؛ النواة المالية منفصلة عن السجل السريري.
