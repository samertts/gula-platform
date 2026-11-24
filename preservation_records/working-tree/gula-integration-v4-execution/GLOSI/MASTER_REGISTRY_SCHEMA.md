# GLOSI Master Registry Schema

**Schema version:** 1.0.0
**Format:** JSON (UTF-8), one canonical file: `REGISTRY/registry.json`
**Validator:** `tools/glosi_registry.py`
**Date:** 2026-11-15

---

## 1. لماذا JSON؟

- قابل للقراءة والتحقق آلياً بدون اعتماديات إضافية (Python stdlib فقط).
- يسمح بتصدير/استيراد كامل دون فقدان البنية.
- لا يحتاج قاعدة بيانات أو خدمة Backend في هذه المرحلة.
- يمكن تحويله لاحقاً إلى JSONL أو قاعدة بيانات دون تغيير المخطط المنطقي.

## 2. البنية العامة

```json
{
  "schema_version": "1.0.0",
  "program": "GLOSI",
  "updated": "YYYY-MM-DD",
  "scoring_model": {
    "weights": {
      "functionality_fit": 15,
      "maturity_stability": 15,
      "security_privacy": 15,
      "interoperability": 15,
      "engineering_quality": 10,
      "license_sustainability": 10,
      "reliability_scalability": 10,
      "cost_maintenance": 5,
      "iraqi_context": 5
    },
    "bands": {
      "excellent": [90, 100],
      "strong_candidate": [80, 89],
      "needs_verification": [70, 79],
      "limited_study": [60, 69],
      "not_recommended": [0, 59]
    }
  },
  "records": []
}
```

`scoring_model` يجب أن يطابق القيم المعتمدة في `EVALUATION_FRAMEWORK.md` حرفياً؛ المدقق يرفض أي اختلاف.

## 3. حقل السجل (Record)

كل سجل كائن مستقل، وله الأقسام التالية إلزامياً:

### 3.1 الهوية `identity`

| الحقل | النوع | إلزامي | القاعدة |
|---|---|---|---|
| `registry_id` | string | نعم | `GLOSI-\d{4}` وفريد |
| `name` | string | نعم | الاسم الرسمي |
| `category` | enum | نعم | رمز من `DOMAIN_TAXONOMY.md` |
| `subcategory` | string | نعم | تصنيف فرعي حر مضبوط |
| `description` | string | نعم | وصف واقعي موجز |
| `official_url` | string | نعم | `https://` |
| `source_type` | enum | نعم | انظر §5 |
| `organization` | string | نعم | الجهة المطوّرة/المشرفة |
| `country` | string | نعم | دولة المقر أو `UNKNOWN` |
| `first_release` | string | نعم | تاريخ/إصدار أول أو `UNKNOWN` |
| `last_verified` | string | نعم | `YYYY-MM-DD` |
| `verification` | object | نعم | `method`, `repository`, `evidence_url`, `release_source`, `retrieved_at`, `archived`, `pushed_at` |

### 3.2 المعلومات التقنية `technical`

| الحقل | النوع |
|---|---|
| `languages` | array<string> |
| `frameworks` | array<string> |
| `architecture` | string |
| `database_support` | array<string> |
| `api_support` | array<string> |
| `interoperability_standards` | array<string> |
| `deployment_options` | array<string> |
| `offline_capabilities` | string |
| `scalability` | string |
| `hardware_requirements` | string |
| `dependencies` | string |
| `latest_verified_version` | string |

القيمة غير المتحقق منها = `UNKNOWN`. يسمح بالمصفوفة الفارغة عند عدم وجود دليل، لكن لا يسمح بقيم تخمينية.

### 3.3 التقييم القانوني `legal`

| الحقل | النوع | ملاحظة |
|---|---|---|
| `license` | string | SPDX أو `UNKNOWN` |
| `license_compatibility` | string | `UNKNOWN` حتى مراجعة قانونية |
| `commercial_use_permission` | string | `PERMITTED` / `RESTRICTED` / `UNKNOWN` |
| `modification_permission` | string | `PERMITTED` / `RESTRICTED` / `UNKNOWN` |
| `redistribution_permission` | string | `PERMITTED` / `RESTRICTED` / `UNKNOWN` |
| `attribution_requirements` | string | `UNKNOWN` عند عدم التحقق |
| `copyleft_obligations` | string | وصف الالتزام أو `NONE` أو `UNKNOWN` |
| `patent_trademark_considerations` | string | `UNKNOWN` افتراضياً |
| `data_licensing_restrictions` | string | خاصة بالبيانات/المصطلحات |
| `review_status` | enum | `NOT_REVIEWED` / `IN_REVIEW` / `REVIEWED` / `BLOCKED` |
| `license_evidence_url` | string | رابط الترخيص/المستودع الذي تم فحصه |

### 3.4 التقييم الأمني `security`

| الحقل | النوع |
|---|---|
| `security_policy` | `VERIFIED` / `NOT_FOUND` / `UNKNOWN` |
| `vulnerability_disclosure` | string |
| `known_cves` | string (ملخص أو `UNKNOWN`) |
| `dependency_risks` | string (`UNKNOWN` حتى SBOM/فحص) |
| `authentication_model` | string |
| `authorization_model` | string |
| `encryption` | string |
| `audit_logging` | string |
| `sbom_availability` | string |
| `maintenance_activity` | string |
| `security_review_status` | enum: `NOT_REVIEWED` / `IN_REVIEW` / `REVIEWED` / `CLEARED` / `BLOCKED` |

### 3.5 التقييم التشغيلي `operational`

| الحقل | النوع |
|---|---|
| `production_usage_evidence` | string |
| `deployment_scale` | string |
| `community_health` | string |
| `release_frequency` | string |
| `maintainer_responsiveness` | string |
| `documentation_quality` | string |
| `test_coverage` | string |
| `ci_status` | string |
| `backup_recovery` | string |
| `upgrade_migration_complexity` | string |

### 3.6 الارتباط بـGULA `gula`

| الحقل | النوع |
|---|---|
| `domain` | string (قسم GULA المستفيد) |
| `component` | string |
| `architecture_layer` | string |
| `integration_possibility` | string |
| `required_adapter` | string |
| `required_api` | string |
| `required_changes` | string |
| `dependencies_on_gula` | string |
| `conflicts_with_existing_components` | string |
| `estimated_integration_cost` | string |
| `expected_benefits` | string |
| `operational_risks` | string |

### 3.7 التقييم `evaluation`

```json
{
  "status": "NOT_EVALUATED | PARTIAL | COMPLETE",
  "confidence": "LOW | MEDIUM | HIGH",
  "dimensions": {
    "functionality_fit": {"score": null, "evidence": []},
    "maturity_stability": {"score": null, "evidence": []},
    "security_privacy": {"score": null, "evidence": []},
    "interoperability": {"score": null, "evidence": []},
    "engineering_quality": {"score": null, "evidence": []},
    "license_sustainability": {"score": null, "evidence": []},
    "reliability_scalability": {"score": null, "evidence": []},
    "cost_maintenance": {"score": null, "evidence": []},
    "iraqi_context": {"score": null, "evidence": []}
  },
  "weighted_total": null,
  "band": null,
  "evaluated_version": "UNKNOWN | <version>",
  "evaluated_at": "YYYY-MM-DD",
  "notes": ""
}
```

القواعد:
- `score` إما `null` أو رقم بين 0 و100. لا صفر بدلاً من `UNKNOWN`.
- `COMPLETE` يتطلب درجة رقمية لكل الأبعاد التسعة، و`weighted_total` محسوباً، و`band` مطابقاً.
- `PARTIAL` يتطلب `weighted_total = null` و`band = null`.
- `evidence` لكل بُعد مصفوفة روابط/مراجع غير فارغة إذا كانت الدرجة رقمية.

### 3.8 القرار `decision`

| الحقل | النوع | القاعدة |
|---|---|---|
| `decision_id` | string | `GLOSI-DEC-\d{4}` وفريد |
| `decision` | enum | `ADOPT` / `INTEGRATE` / `ADAPT` / `REIMPLEMENT` / `STUDY` / `MONITOR` / `REJECT` |
| `status` | enum | `PROPOSED` / `APPROVED` / `REJECTED` / `DEFERRED` / `SUPERSEDED` |
| `date` | date | `YYYY-MM-DD` |
| `owner` | string | المالك المسؤول |
| `reviewers` | object | `technical`, `security`, `legal` — كل منها اسم أو `UNASSIGNED` |
| `evidence` | array<string> | غير فارغة |
| `adr_reference` | string \| null | مطلوب عند `APPROVED` |
| `rationale` | string | سبب القرار بالعربية أو الإنجليزية |

قيود إضافية:
- `APPROVED` يتطلب `evaluation.status = COMPLETE`، و`license != UNKNOWN`، و`security_review_status` في `REVIEWED`/`CLEARED`، ومراجعين معينين، و`adr_reference`.
- `ADOPT`/`INTEGRATE`/`ADAPT` مع `status = APPROVED` ممنوعة إذا كان `license_compatibility = INCOMPATIBLE` أو `security_review_status = BLOCKED`.
- `REJECT` يتطلب `rationale` غير فارغ.
- القرارات الأولية في الدفعة الأولى هي `PROPOSED` فقط وغير ملزمة.

### 3.9 تاريخ التقييم `evaluation_history`

مصفوفة إلزامية (يمكن أن تكون فارغة فقط لحالة `NOT_EVALUATED`):

```json
[
  {
    "date": "YYYY-MM-DD",
    "version": "UNKNOWN",
    "evaluation_status": "PARTIAL",
    "summary": "سبب التحديث أو موجز النتيجة",
    "evidence_refs": ["https://..."]
  }
]
```

لا يُحذف أي عنصر. التحديث يضيف عنصراً جديداً.

## 4. العلاقات

- `registry_id` → `decision.decision_id` علاقة 1:1 داخل السجل.
- `decision.adr_reference` يشير إلى ADR داخل `docs/adr/` عند الاعتماد.
- `evaluation_history[].evidence_refs` تشير إلى `REPORTS/evidence/` أو مصدر رسمي.
- `gula.component` يشير إلى مكوّن قائم في `backend/app/` أو `frontend-v3/` عند الوجود؛ وإلا `UNKNOWN`.

## 5. التعدادات المعتمدة

**source_type:**
`open_source_repository`, `library_framework`, `research_paper`, `systematic_review`,
`clinical_study`, `technical_documentation`, `international_standard`,
`government_implementation`, `national_program`, `security_advisory`, `benchmark`,
`case_study`, `dataset`, `simulation_environment`.

**category:**
`A_health_systems`, `B_laboratory`, `C_public_health`, `D_standards_interoperability`,
`E_identity_security_privacy`, `F_infrastructure_reliability`, `G_artificial_intelligence`,
`H_government_national`.

## 6. قواعد التحقق الآلي

يفشل المدقق (`FAIL`، exit code 1) عند:
1. JSON غير صالح أو حقل إلزامي ناقص.
2. `registry_id` مكرر أو بصيغة خاطئة.
3. `official_url` غير HTTPS.
4. قيمة enum غير معتمدة.
5. وزن/نطاق تقييم لا يطابق `EVALUATION_FRAMEWORK.md`.
6. درجة خارج 0–100 أو `weighted_total` غير مطابق.
7. `COMPLETE` بدرجات ناقصة أو `PARTIAL` بدرجة كلية.
8. قرار `APPROVED` بلا تقييم مكتمل/مراجعين/ADR.
9. اعتماد مع ترخيص `UNKNOWN` أو أمن `BLOCKED`.
10. سجل PARTIAL بلا `evaluation_history`.
11. تصدير/استيراد لا يعيد نفس البنية (اختبار مستقل).

## 7. التصدير والاستعادة

- التصدير: `python GLOSI/tools/glosi_registry.py export GLOSI/REGISTRY/registry.json`
- التحقق بعد الاستعادة: نفس الأمر `validate` + مقارنة SHA-256 للملف المصدّر.
- الصيغة المفتوحة الوحيدة المطلوبة الآن هي JSON؛ لا توجد قاعدة بيانات.
