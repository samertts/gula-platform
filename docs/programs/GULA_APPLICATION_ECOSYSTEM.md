# GULA — Application Ecosystem

## قاعدة المنظومة

تتكون المنظومة من تطبيق واحد لكل منصة، وتظهر المجالات كـWorkspaces داخل GULA. لا تُنشأ حسابات مستقلة للمواطن والطبيب والمختبر والصيدلية والمستشفى؛ الحساب الموحد يحمل العضويات والأدوار والسياق والامتيازات المسموح بها.

| المنصة | المسار الحالي | الغرض الفعلي | الحالة | الخطوة التالية |
|---|---|---|---|---|
| Web | `frontend-v3` | واجهة React/Vite/PWA الحديثة مع shell وGuide Assistant وواجهات API | IMPLEMENTED/PARTIAL | توحيد workspace/context، E2E، accessibility، offline sync |
| Android | `mobile/android` | أساس Android/Kotlin وعقود API | PARTIAL | بناء CI، secure session، Room/sync، tests، signing |
| iOS | مصادر/أساسات متعددة بحسب المستودع | أساس native غير مثبت كإصدار | PARTIAL/NOT VERIFIED | جرد المسار الفعلي ثم CI native وTestFlight gates |
| Desktop | `mobile/desktop` و`hospital_desktop` | Flutter Desktop/تشغيل مستشفى عند الحاجة | PARTIAL | تحديد المسار المعتمد، analyzer/printing/offline، Windows build |
| Demo Web | Web + Backend demo | مشاهدة عامة ببيانات اصطناعية معزولة | IMPLEMENTED | نشر منفصل بقاعدة/Redis/secrets وnetwork isolation |

## Workspaces المستهدفة

المواطن، السريري، المختبر، الأشعة، الصيدلية، المستشفى، الطوارئ/EMS، بنك الدم، الصحة العامة، القوى العاملة، خدمات الموظفين، تشغيل المنشأة، المديرية، الوزارة/التحكم الوطني، البحث، الإدارة، والشركاء المصرحون. لا يعني وجود اسم المجال في الكود أن capability مكتملة أو مصدقة.

## الخدمات المشتركة

كل التطبيقات تستخدم خدمة هوية وجلسات، authorization server-side، workspace/context switching، search، notifications، inbox/tasks، documents، consent/privacy، help/localization/accessibility، API contracts، audit، feature flags، sync، وobservability. لا يجوز إعادة بناء هذه الخدمات داخل كل مجال.

## مصفوفة المجالات

| المجال | ما هو موجود حالياً | الفجوة أو القيد |
|---|---|---|
| Citizen/Clinical | registration، patient/lab routes، صفحات واجهة ومساعد | تجربة موحدة وresource-level E2E غير مكتملة |
| Laboratory | orders/samples/results/validation/QC ومهاجرات | CAS الكامل، analyzer gateway، production integration |
| Radiology | models/routes ومراجع DICOM/RIS/PACS | تكامل فعلي sandbox وإثبات سلامة |
| Pharmacy/Hospital/EMS/Blood/Public Health | modules/models/configs بدرجات متفاوتة | readiness matrix ومحركات مشتركة ومراجعة سريرية |
| Workforce/Ministry | governance/identity/national modules | فصل HR عن clinical وإثبات control-plane workflows |
| AI/Analytics | RAG/evaluation/AI platform وguardrails | human oversight، provenance، kill switch وproduction governance |
| Integration | FHIR/DHIS2/DICOM ومسارات external | mapping/terminology hub موحد وعقود versioned |

## سياسة الإصدار

لا يُنشر Android أو iOS أو Windows EXE أو production Web release لمجرد وجود المصدر. يلزم build reproducible، اختبارات، signing، permissions/privacy declarations، rollback، ونتيجة CI. لا يُنشر GitHub Release أو تغيير deployment behavior ضمن Wave 0/1 دون اعتماد مستقل.
