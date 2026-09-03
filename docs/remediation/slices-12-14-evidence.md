
--- FULL SUITE ---
2836 passed, 5 skipped, 165 warnings (330.92s)

# Evidence — Slices 12–14

## PostgreSQL disposable

PostgreSQL 16.15 قاعدة اختبار محلية disposable فقط. `alembic upgrade head` وصل إلى `20260828_0019`. ثم نجح `alembic downgrade 20260828_0018` وإعادة `upgrade head`.

Schema gate أثبت وجود 11 جدولاً جديداً على الأقل من Finance/LIS/Pharmacy، و`core_financial_bills.coverage_id`، و`core_financial_payment_events.nonce` مع unique constraint، و`core_financial_bills.ck_fin_bill_total`، وFKs لسجل recalls وindex coverage.

## Tests

Focused slices: `17 passed, 1 warning`.
Full backend suite بعد التعديلات الحالية: `2836 passed, 5 skipped, 165 warnings` خلال `330.92s`.

## Quality

compileall، Ruff على الملفات المعدلة، و`git diff --check` نجحت. الفحص العام لـRuff على كامل `app/` ما زال يكشف أخطاء legacy غير مرتبطة في `app/contracts/models.py` و`app/contracts/routes.py`؛ لم تُنسب إلى هذه Slices ولم تُخفَ.

Secret scan النصي لم يجد credential تشغيلية جديدة؛ ظهرت فقط أنماط اختبار/توثيق مقصودة في bandit fixture و`docs/DEPLOYMENT.md`.

## Readiness

`production_ready=false` و`golden_path_passed=false`. لا provider حي، لا بيانات حقيقية، لا worker/polling، ولا staging/remote-CI proof جديد. PR #250 يجب أن يبقى Draft.
