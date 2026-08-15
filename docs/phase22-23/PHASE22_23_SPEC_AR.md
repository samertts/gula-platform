# مواصفة Phase 22 وPhase 23 — Universal Accessibility وUnified Settings

**المالك التشغيلي:** GULA Platform

**الحالة:** جاهز للمراجعة البرمجية والأمنية، مع عناصر مصنفة `BACKEND_DEPENDENCY` و`LEGAL_REVIEW` لا يجوز اعتبارها مكتملة قبل اعتماد العقود أو الترجمة.

**النطاق:** هذه المواصفة تكمل Phase 21 ولا تبدأ Phase 24. وهي تغطي الويب/PWA وتوثق parity المطلوبة على Android وiOS وFlutter Desktop، مع إبقاء نشر المتاجر خارج النطاق.

> **قاعدة السلامة:** إعدادات Accessibility تغيّر طريقة العرض والتفاعل فقط. لا تشخّص حالة صحية، ولا تمنح Role أو Permission، ولا تتجاوز Backend Authorization أو عزل المختبر أو تدقيق العمليات.

## 1. المبادئ غير القابلة للتجاوز

يجب أن تكون كل حالة واجهة مفهومة دون الاعتماد على اللون وحده؛ لذلك تستخدم المنصة **اللون والنص والأيقونة والشكل** معًا في الحالات التشغيلية. ويجب أن تبقى عمليات السجل السريري خاضعة لعقد backend، ونسخة البيانات، وRBAC، وworkspace/lab scope، وAudit Log. لا يجوز أن يؤدي فشل تحميل تفضيلات Accessibility إلى إخفاء عناصر السلامة؛ سلوك الواجهة في هذه الحالة fail-open بالنسبة للوظائف السريرية، مع تسجيل خطأ تقني غير حساس.

Health Preferences ليست Accessibility Profile. فهي معلومات حساسة اختيارية لا تحفظ إلا بعد موافقة صريحة، وتظل في backend مشفرة ومراجعة بالإصدار والتدقيق. لا تستخدم الأجهزة المحلية لتخزين محتوى صحي، ولا تُنشأ بيانات صحية وهمية أو استنتاجات تشخيصية.

## 2. Accessibility Center — Phase 22

مسار الويب هو `/settings/accessibility`. الصفحة مستقلة عن Settings Home وتوفر Preview حيًا قبل Apply، مع أزرار Save وCancel. التغيير في أي toggle يفعّل preview محليًا للعرض فقط، ولا يكتب إلى backend حتى يضغط المستخدم Save. Cancel يعيد القيم المحفوظة ويزيل preview.

يستعمل المركز مكونات `AdaptiveStateBadge` و`AdaptiveStatus` و`AdaptivePreview`. الحالات المدعومة هي `Enabled` و`Disabled` و`Preview` و`Saved` و`Saving` و`Failed` و`Consent Required` و`Permission Denied` و`Unavailable` و`Offline`. الحالة التي لا تملك عقد API تعرض `BACKEND_DEPENDENCY` بدل زر وهمي.

| الفئة | التغطية | السلوك الآمن | حالة Phase 22 |
|---|---|---|---|
| Visual | التباين، الاعتماد على اللون، القراءة الميسرة، حجم النص، مقياس النص، color-blind mode | إضافة نص/أيقونة/شكل وعدم تغيير صلاحيات البيانات | `READY` |
| Hearing | captions، visual alerts، transcripts، mute-safe notifications | عدم إسقاط التنبيه الحرج عند تفعيل تقليل الإشعارات | `READY` |
| Motor | أهداف لمس أكبر، تعقيد أقل، مهلة أطول، keyboard navigation | لا يغيّر قواعد workflow السريري أو state machine | `READY` |
| Cognitive / Reading | واجهة مبسطة، كثافة أقل، لغة واضحة، خطوات متسلسلة | لا يحذف عناصر السلامة ولا يخفي validation | `READY` |
| Photosensitivity | reduced motion، disable flashing، static alternatives، reduced notifications | لا توجد تأثيرات وميض مقصودة؛ البديل الثابت إلزامي عند توفره | `READY` |
| Communication | text alternatives، voice interaction، screen-reader optimized | يعرض حالة الدعم بدل الادعاء بأن كل جهاز يملك تكاملًا صوتيًا | `READY` جزئيًا |

## 3. Settings Home — Phase 23

مسار الويب هو `/settings`. يعرض Settings Home مصفوفة مصنفة من أربعة عشر قسمًا. الأقسام الجاهزة تربط إلى route موجود أو إلى Accessibility Center. الأقسام التي لا توجد لها API لا تخترع مسارًا ولا تعرض بيانات تجريبية؛ بل تعرض `BACKEND_DEPENDENCY` مع وصف السبب.

| القسم | UI Route | API/Contract | Permission | Scope | Audit | Consent | Feature Flag | الحالة وخطأ الفشل |
|---|---|---|---|---|---|---|---|---|
| Account | `/profile` | Profile contract الحالي | مستخدم موثق | User | حسب عمليات profile | لا | لا | `READY`; 401 يعيد إلى login |
| Identity | `/profile` | Profile/identity الحالي | مستخدم موثق، وتفويض الدور حيث يلزم | User/Lab | نعم عند التغيير | لا | لا | `READY`; Permission Denied من backend |
| Language | `/settings` | LocaleContext وi18next | مستخدم/جلسة | User/Device UI | تغيير العرض فقط | لا | لا | `READY`; fallback إلى en عند غياب resource |
| Appearance | `/settings/accessibility#display-profile` | Accessibility contract | مستخدم موثق | User | عند حفظ profile | لا | لا | `READY`; Preview لا يكتب |
| Accessibility | `/settings/accessibility` | `GET/PUT /user-preferences/accessibility` | مستخدم موثق | User | إصدار وتغيير profile | لا | لا | `READY`; `Failed` أو `Offline` دون كسر الوظائف السريرية |
| Health Preferences | `/settings#health-preferences` | `GET/PUT/DELETE /user-preferences/health` | مستخدم موثق | User، مع lab isolation | consent وversion وaudit | موافقة صريحة وإصدار consent | لا | `READY` مشروط؛ `Consent Required` أو `Conflict` |
| Privacy | `/privacy-policy` | مستند قانوني موجود | عام | Global | لا تغيير من الصفحة | حسب المستند | لا | `READY`; المستند ثابت وقابل للمراجعة |
| Security | `/security` | Security page الحالي | `RoleGuard` وBackend authorization | Lab/Admin scope | نعم | لا | لا | `READY` للدور؛ `Permission Denied` لغيره |
| Notifications | لا يوجد | لا يوجد عقد موحد | غير متاح | — | — | — | لاحقًا | `BACKEND_DEPENDENCY`؛ لا زر وهمي |
| Devices / Sessions | لا يوجد | لا يوجد contract لإدارة الجلسات | غير متاح | User | — | — | لاحقًا | `BACKEND_DEPENDENCY`؛ لا كشف لجلسات غير موجودة |
| Workspaces | لا يوجد في Settings API | workspace APIs موجودة لسياقات العمل فقط | حسب RoleGuard وscope | Workspace/Lab | حسب العمليات الحالية | لا | لاحقًا | `BACKEND_DEPENDENCY`؛ لا تغيير scope من الواجهة |
| Memberships | لا يوجد | IAM contract غير مكشوف لهذا المركز | IAM/إداري | Lab/Org | نعم عند توفر العقد | لا | لاحقًا | `BACKEND_DEPENDENCY` |
| Services | لا يوجد | Integrations تحتاج عقودًا ومراجعة | Admin/Connector scope | Organization | نعم | حسب التكامل | لاحقًا | `BACKEND_DEPENDENCY` و`SECURITY_REVIEW` قبل أي اتصال |
| Help | لا يوجد route دعم موحد | لا يوجد contract | عام/موثق | Global | — | لا | لاحقًا | `BACKEND_DEPENDENCY` |

## 4. العقود والخصوصية والتدقيق

العقد الحالي لـAccessibility Profile يستخدم `GET /user-preferences/accessibility` و`PUT /user-preferences/accessibility`. يعيد GET قيمًا آمنة افتراضية عند عدم وجود profile، ويعيد PUT نسخة محدثة. يجب أن يظل التحديث مرتبطًا بالمستخدم الموثق، وأن يرفض backend أي user أو lab scope يأتي من جسم الطلب بدل الجلسة الموثقة.

العقد الحالي للاحتياجات الصحية يستخدم `GET /user-preferences/health` و`PUT /user-preferences/health` و`DELETE /user-preferences/health`. الكتابة تتطلب `consent=true` و`consent_version`، وتدعم version conflict، أما الحذف فيسحب الموافقة ويحذف payload المشفر. لا يحق لواجهة frontend اعتبار النجاح محققًا قبل استجابة backend.

| الحدث | البيانات الدنيا | ما يجب عدم تسجيله |
|---|---|---|
| Accessibility profile updated | actor/user id، timestamp، version، action، outcome | لا health payload ولا token |
| Health consent granted | actor/user id، consent version، timestamp، outcome | لا plaintext health values |
| Health consent revoked | actor/user id، timestamp، deletion outcome | لا payload قبل الحذف |
| Permission denied | actor، route، scope decision، timestamp، correlation id | لا أسرار أو محتوى سريري زائد |
| Offline/failed save | session correlation، route، state، error class | لا بيانات حساسة أو نصوص صحية |

## 5. اللغات والاتجاه

توجد سبعة رموز في catalog: `ar-IQ` و`ar` و`en` و`ku` و`tk` و`syr` و`fa`. حاليًا توجد resources مراجعة للغات الخمس الأساسية الموجودة في المشروع. يعمل `ar-IQ` على resource العربية الحالية، و`fa` على fallback إنجليزي مؤقت؛ لذلك لا يجوز تسويق ذلك كترجمة فارسية أو عراقية مكتملة. حالة هذين الرمزين هي `LEGAL_REVIEW` و`TRANSLATION_REVIEW` إلى أن تضاف موارد مترجمة وتُراجع المصطلحات الطبية والقانونية.

يجب اختبار اتجاه `rtl` لكل من العربية والكردية والسريانية والفارسية، واتجاه `ltr` للإنجليزية والتركمانية وفق catalog. يجب ألا يسبب تغيير اللغة حذف draft أو إرسال Health Preferences، ولا يجب أن يغير اللغة Role أو scope.

## 6. مصفوفة QA المشتركة

| السطح | نطاق العرض | الاختبارات الأساسية | شرط القبول |
|---|---:|---|---|
| Web/PWA | 320، 375، 768، 1024، 1440، 1920px | overflow، keyboard، focus، preview، reduced motion، status non-color | لا قص أفقي، كل عنصر قابل للوصول، لا تغيير API قبل Save |
| Android | شاشات هاتف صغيرة وكبيرة | touch targets، TalkBack، reduced motion، offline fail-safe | لا local health payload، وRBAC لا يتغير |
| iOS | iPhone SE إلى iPad | Dynamic Type، VoiceOver، static alternatives، update gate | لا publish؛ build checks تمر، وإعدادات العرض منفصلة عن health |
| Flutter Desktop | Linux/macOS/Windows CI | keyboard، scaling، contrast، state labels | عدم كسر build، ولا تخزين صحي محلي |
| Locales | الرموز السبعة | تغيير locale، direction، fallback، حفظ Accessibility | لا crash؛ الموارد غير المكتملة معلّمة ولا تدّعي اكتمالًا |
| Security | unauthenticated وwrong scope | 401/403، lab isolation، conflict، audit | لا side door ولا frontend-only authorization |

## 7. تصنيف الجاهزية

`READY` تعني أن الواجهة والعقد الحاليين قابلان للاختبار دون اختراع API جديد. `BACKEND_DEPENDENCY` تعني أن الواجهة تعرض حدودها بوضوح ولا تنفذ أي كتابة أو قراءة غير معتمدة. `SECURITY_REVIEW` مطلوبة قبل أي تكامل خارجي أو إدارة جلسات أو عضويات. `LEGAL_REVIEW` مطلوبة للموارد اللغوية غير المراجعة ولأي نص يتصل بالموافقة والخصوصية. `BLOCKED` تعني عدم السماح بالتنفيذ حتى تتوفر الاعتمادية؛ لا توجد في Accessibility Center الجاهزة، لكن قد تظهر في CI أو release gate إذا غاب contract.

## 8. Release gate

لا تنتقل المنصة إلى Phase 24 قبل إكمال typecheck وlint وunit tests وproduction build واختبارات backend الخاصة بتفضيلات المستخدم والتحديثات والأبواب الجانبية. كما يجب أن تبقى حماية branch وPR review كما هي، وألا يتم تجاوز collaborator approval. هذا التغيير لا ينشر إلى App Store أو Google Play أو Microsoft Store، بل يجهز السطح البرمجي فقط.

## المراجع

[1]: https://www.w3.org/TR/WCAG22/ "Web Content Accessibility Guidelines (WCAG) 2.2"
[2]: https://github.com/samertts/gula-platform "GULA Platform repository"
[3]: https://fastapi.tiangolo.com/ "FastAPI documentation"
