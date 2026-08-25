# Testing Strategy

> **حالة الدليل:** في 25 أغسطس 2026، نجح التشغيل المحلي المعتمد من `backend/` بالأمر `pytest -q` بنتيجة **2742 passed, 4 skipped, 249 warnings** خلال 189.30 ثانية. هذه نتيجة محلية قابلة لإعادة التشغيل، وليست دليلاً على CI خارجي أو staging أو قرار إطلاق. يبقى الإطلاق **NO-GO** إلى اكتمال جميع أدلته المستقلة.

## Test Suite Overview

| Category | Files | Tests | Purpose |
|----------|-------|-------|---------|
| Unit | 25 | 400+ | Service, model, domain logic |
| Integration | 10 | 200+ | Route, DB, cross-module |
| Security | 3 | 54+ | Auth, JWT, encryption, RBAC |
| Regression | 5 | 100+ | Stability, concurrency, chaos |
| Skills | 15 | 100+ | Skill platform lifecycle |
| Performance | 2 | 50+ | Stress, performance budgets |

## Running Tests

```bash
# الحزمة الخلفية المعتمدة محلياً
cd backend && pytest -q

# تغطية محلية؛ لا تعني بلوغ عتبة إطلاق أو حسم تعارض سياسة التغطية
cd backend && pytest -q --cov=app --cov-report=term-missing

# اختبارات الأمن الموجهة
cd backend && pytest -q tests/test_security.py tests/test_security_regression.py

# اختبارات التكامل الموجودة
cd backend && pytest -q tests/integration/

# اختبار منفرد
cd backend && pytest -q tests/test_security.py::TestJWTTokens::test_invalid_token_returns_none
```

> لا تستخدم `pytest -q` من جذر المستودع كبديل للحزمة الخلفية؛ فهو قد يجمع اختبارات خدمات وbridge ذات تهيئة واستيرادات مستقلة. نفّذ اختبارات تلك الخدمات من أدلتها ومساراتها الخاصة.

## Quality Gates

### Gate A: Backend Foundation
- **Ruff lint**: 0 errors
- **Ruff format**: All files formatted
- **PyCompile**: All files compile
- **Tests**: آخر تشغيل backend محلي معتمد: 2742 passed, 4 skipped, 249 warnings (25 أغسطس 2026). لا يعد هذا بديلاً عن CI خارجي.

### Gate B: Security
- **Bandit**: 0 High, 2 Medium (dev config only), 53 Low
- **Security tests**: 54+ passing
- **No permission bypasses**: Verified

### Gate C: Testing
- **Coverage**: لا تعتمد هذه الوثيقة رقماً لإثبات الجاهزية. يجب قياس التغطية في تنفيذ مستقل مع توثيق الأمر والـcommit ونطاق الاستبعاد، ثم حسم تعارض العتبات حوكمياً.
- **High-coverage modules**: لا تُعامل الادعاءات التاريخية كنسبة حالية بلا تقرير coverage متكرر.
- **Known gaps**: يلزم قياس routes/services/edge/interoperability في تقرير قابل لإعادة التشغيل قبل وضع أرقام جديدة.

### Gate D: Production Readiness
- لا يجوز وصف بوابات الجودة بأنها خضراء بالكامل استناداً إلى دليل محلي.
- يلزم نجاح CI خارجي، وأدلة أمن/معمارية قابلة للمراجعة، وstaging migration مع backup/restore، وAndroid موقّع، وUAT، وتوقيعات مخولين قبل قرار GO.
- يبقى الوضع الافتراضي **NO-GO** عند غياب أي دليل أو توقيع مطلوب.

## Test Markers

```python
@pytest.mark.unit          # Fast, isolated unit tests
@pytest.mark.integration   # Tests requiring DB or multiple modules
@pytest.mark.security      # Security-focused tests
@pytest.mark.stress        # Performance/load tests
```

## Coverage Targets

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| security/ | 65% | 80% | High |
| models/ | 90% | 95% | High |
| routes/ | 35% | 60% | Medium |
| services/ | 30% | 50% | Medium |
| integration/ | 70% | 85% | High |
| edge/ | 25% | 50% | Low |

## Known Issues

1. **الادعاء التاريخي عن 268 خطأ و3 إخفاقات**: لم يظهر في التشغيل المحلي المعتمد من `backend/` في 25 أغسطس 2026. لا يعني ذلك أن مسار جذر المستودع أو اختبارات الخدمات المستقلة صالحة؛ فهي نطاقات منفصلة يجب تهيئتها وتشغيلها وفق أدلتها.
2. **249 تحذيراً**: التشغيل الحالي ينتهي بتحذيرات deprecation معروفة في FastAPI/Starlette و`datetime.utcnow()` وSQLAlchemy ومكونات أخرى. لا تخفِ التحذيرات أو تعطلها؛ سجلها كدين منفصل وأصلحها في دفعات محددة.
3. **أدلة الإطلاق**: نجاح pytest المحلي لا يغلق CI أو التغطية أو الأمن أو المهاجرات أو UAT أو التوقيعات البشرية.
