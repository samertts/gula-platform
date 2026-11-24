# GLOSI — Global Library of Open Solutions & Intelligence

**Program:** GLOSI Master Registry
**Status:** Phase 0–2 PASS; Phase 3–4 PARTIAL; Phase 5 initiation report published; no project approved
**Owner:** GULA Architecture & Governance (proposed)
**Scope:** Independent knowledge registry that feeds GULA architecture, security, and procurement decisions — without modifying GULA Core.

---

## 1. التعريف

GLOSI سجل مركزي منظّم للمعرفة التقنية والعلمية والتشغيلية العالمية التي يمكن أن تستفيد منها منصة GULA الوطنية. لا يجمع GLOSI أكبر عدد من المشاريع، بل يحدد الحلول الأفضل، ويقيّمها بالأدلة، ويوثّق قرار الاستفادة منها أو رفضها، ويحافظ على قابلية التتبع والمراجعة.

GLOSI **ليس** متجراً للبرمجيات، ولا آلية دمج تلقائي. هو طبقة بحث وحوكمة تقف **قبل** أي قرار معماري في GULA.

## 2. الأهداف

1. تقليل تكرار تطوير وظائف موجودة في مشاريع ناضجة.
2. رفع الأمن والاعتمادية وجودة البيانات عبر تقييم موحد.
3. حماية السيادة الرقمية العراقية والاستضافة المحلية.
4. خفض التكلفة الكلية لدورة حياة النظام.
5. إنتاج أدلة قابلة للتحقق تدعم قرارات ADR.
6. منع التبعية التقنية أو القانونية أو المالية لمزوّد واحد.

## 3. النطاق

يشمل السجل: الأنظمة الصحية والسجلات الطبية، المختبرات، الصحة العامة والترصد، المعايير والتبادل الصحي، الهوية والأمن والخصوصية، البنية التحتية والاعتمادية، الذكاء الاصطناعي، والإدارة الحكومية الوطنية. يغطي المصادر مفتوحة المصدر، المكتبات، الأبحاث، المراجعات المنهجية، المعايير الدولية، البرامج الحكومية، النشرات الأمنية، والبيانات العامة.

التصنيفات التفصيلية في [`DOMAIN_TAXONOMY.md`](DOMAIN_TAXONOMY.md).

## 4. طريقة الاستخدام

1. اقرأ [`GOVERNANCE.md`](GOVERNANCE.md) و[`EVALUATION_FRAMEWORK.md`](EVALUATION_FRAMEWORK.md).
2. تحقق من وجود السجل مسبقاً في [`REGISTRY/registry.json`](REGISTRY/registry.json).
3. أضف/حدّث السجل وفق [`MASTER_REGISTRY_SCHEMA.md`](MASTER_REGISTRY_SCHEMA.md).
4. شغّل المدقق المحلي:

```bash
python3 GLOSI/tools/glosi_registry.py validate GLOSI/REGISTRY/registry.json
python3 -m unittest discover -s GLOSI/tests -v
```

5. لا يُعتبر أي سجل معتمداً إلا بعد استكمال مسار المراجعة في [`INTEGRATION_POLICY.md`](INTEGRATION_POLICY.md) وإصدار قرار في [`DECISION_RECORDS/`](DECISION_RECORDS/) وربطه بـADR عند الحاجة.

## 5. المبادئ الحاكمة

- **الدليل قبل الدرجة:** لا درجة بلا دليل، و`UNKNOWN` لا يتحول إلى صفر أو نجاح.
- **الفصل عن GULA Core:** GLOSI لا يغيّر الكود أو قاعدة البيانات أو الصلاحيات تلقائياً.
- **الترخيص أولاً:** لا افتراض بأن المصدر العام يعني إعادة استخدام حرة.
- **الأمن أولاً:** أي خطر أمني حرج يوقف الاعتماد بغضّ النظر عن الدرجة.
- **الاستبدال:** كل مكوّن خارجي يجب أن يبقى قابلاً للاستبدال.
- **الشفافية:** كل ادعاء تقني مرتبط بمصدر وتاريخ تحقق.
- **الاستقلالية:** لا خدمات مدفوعة أو مفاتيح API في هذه المرحلة.

## 6. الهيكل

| المسار | الغرض |
|---|---|
| `README.md` | التعريف والأهداف والاستخدام |
| `GOVERNANCE.md` | الأدوار والصلاحيات وقواعد الاعتماد |
| `MASTER_REGISTRY_SCHEMA.md` | مخطط السجل وقواعد التحقق |
| `EVALUATION_FRAMEWORK.md` | النموذج من 100 نقطة ومستويات الثقة |
| `SOURCE_CATALOG.md` | المصادر الرسمية وموثوقيتها |
| `DOMAIN_TAXONOMY.md` | تصنيف المجالات الصحية والتقنية |
| `INTEGRATION_POLICY.md` | ضوابط الاستفادة والربط مع GULA |
| `SECURITY_AND_LICENSE_POLICY.md` | مراجعة الأمن والتراخيص |
| `ROADMAP.md` | المراحل والمهام المستقبلية |
| `REGISTRY/registry.json` | السجل الآلي (المصدر الرسمي) |
| `DECISION_RECORDS/` | قرارات التقييم والاعتماد |
| `REPORTS/` | تقارير المراحل والأدلة |
| `tools/` | مدقق وتصدير السجل |
| `tests/` | اختبارات سلامة السجل |

## 7. الحالة الحالية

- **Phase 0 (Discovery):** مكتملة — لا يوجد سجل GLOSI سابق؛ تمت إعادة استخدام أصول البحث الموجودة.
- **Phase 1 (Governance):** مكتملة — الحوكمة والسياسات ونموذج التقييم.
- **Phase 2 (Registry):** PASS — المخطط والمدقق والاختبارات والسجل الآلي.
- **Phase 3 (Initial Research):** PARTIAL — 16 مورداً بأدلة تحقق من المصدر؛ التقييم الكامل `PARTIAL` والثقة `LOW`.
- **Phase 4 (Quality Assurance):** PARTIAL — فحوص آلية PASS؛ المراجعة الأمنية والقانونية البشرية `NOT RUN`.
- **Phase 5 (Program Initiation):** PASS — تقرير التأسيس وملفات القرارات المقترحة منشورة في `REPORTS/` و`DECISION_RECORDS/`.

**لا يوجد مشروع معتمد أو مدمج في GULA نتيجة هذا السجل.** كل القرارات الحالية مقترحة وغير ملزمة.

## 8. المراجع المؤسسية

- `GOVERNANCE/GULA_STABLE_V1_PROGRAM_CHARTER.md`
- `GOVERNANCE/AI_AGENT_RULES.md`
- `docs/architecture/OPEN_SOURCE_POLICY.md`
- `docs/architecture/VENDOR_LOCK_IN_POLICY.md`
- `docs/architecture/FREE_FIRST_POLICY.md`
- `docs/health-tech/TRANSFER_CANDIDATES_AND_INTEGRATION_ROADMAP_AR.md`
- `docs/discovery/GLOBAL_HEALTHCARE_ATLAS.md`
