# دليل وثائق GULA Platform

هذا الفهرس هو **نقطة الدخول إلى وثائق المشروع**. ابدأ بالمسار الأقصر المناسب لدورك، ثم انتقل إلى المراجع التفصيلية عند الحاجة. تبقى الوثائق والتقارير التاريخية في مواضعها الحالية للحفاظ على قابلية التتبع والروابط القديمة.

| إن كنت تريد… | ابدأ هنا | ثم انتقل إلى |
|---|---|---|
| تشغيل المشروع أو المساهمة فيه | [Start Here](START_HERE.md) | [دليل المساهمة](../CONTRIBUTING.md) و[دليل الاختبارات](testing/) |
| إصدار تغيير بأمان | [دليل Staging](STAGING_RUNBOOK.md) | [إرشادات النشر](deployment/) و[دليل الإنتاج](production/) |
| تشغيل تجربة LIS والتشغيل البيني | [دليل تجربة LIS](LIMS_PILOT_RUNBOOK_AR.md) | [استراتيجية FHIR](architecture/ADR-011-fhir-strategy.md) ودستور البيانات |
| فهم البنية التقنية | [العمارة](architecture/) | [قرارات البنية](adr/) و[واجهات API](api/) |
| مراجعة الضوابط الأمنية | [الأمن](security/) | [سياسة الإبلاغ](../SECURITY.md) و[الهندسة التشغيلية](operations/) |
| العمل على نطاق صحي أو تشغيلي | [النطاقات](domain/) | [الرعاية الصحية](healthcare/) و[NIAM](niam/) |
| فهم قرارات الإصدار والجودة | [الإصدارات](release/) | [الجودة](quality/) و[الأداء](performance/) |

## خريطة الوثائق

| المجال | المحتوى |
|---|---|
| **البدء والهندسة** | [Start Here](START_HERE.md)، [architecture](architecture/)، [engineering](engineering/)، [api](api/) |
| **التشغيل والإطلاق** | [deployment](deployment/)، [operations](operations/)، [runbooks](runbooks/)، [production](production/)، [testing](testing/) |
| **الأمن والامتثال** | [security](security/)، [governance](governance/)، [standards](standards/)، [trust](trust/) |
| **المنتج والمنصات** | [platform](platform/)، [frontend](frontend/)، [pharmacy-platform](pharmacy-platform/)، [radiology-platform](radiology-platform/)، [nursing-platform](nursing-platform/) |
| **البيانات والتكامل** | [database](database/)، [events](events/)، [api](api/)، [niam](niam/)، [دليل تجربة LIS](LIMS_PILOT_RUNBOOK_AR.md) |
| **القياس والجودة** | [performance](performance/)، [metrics](metrics/)، [quality](quality/)، [technical-debt](technical-debt/) |
| **السجل والقرارات** | [adr](adr/)، [decisions](decisions/)، [release](release/)، [reports](reports/) |
| **البحث والخطط** | [research](research/)، [roadmap](../ROADMAP.md)، [programs](programs/) |

## وثائق الجذر التاريخية

توجد في جذر المستودع تقارير وشهادات ومراجع صادرة ضمن مراحل سابقة. لا تُعد هذه الصفحات بديلاً عن الأدلة التشغيلية أعلاه. عند الحاجة إلى تقرير محدد، استخدم [سجل التغييرات](../CHANGELOG.md)، أو راجع مجلد [التقارير](reports/) أولاً، ثم انتقل إلى الملف التاريخي المرتبط.

## مبادئ التنظيم

> استخدم `docs/` للوثائق الجديدة الدائمة، وضع دليل التشغيل في `docs/runbooks/` أو أضف رابطاً إليه من هذا الفهرس، واحتفظ بتقارير التنفيذ المؤرخة في `docs/reports/`. لا تنقل وثيقة جذرية أو تاريخية إلا مع تحديث جميع روابطها واختبارها.

للملاحظات المتعلقة بالوثائق، افتح طلباً من قالب [توثيق](../.github/ISSUE_TEMPLATE/documentation.md) أو قدّم تحسيناً عبر [دليل المساهمة](../CONTRIBUTING.md).
