# تقرير تدقيق تجربة Mobile App-Like وPWA لمنصة GULA

**المشروع:** GULA National Health Platform

**النطاق:** `frontend-v3`

**التاريخ:** 14 أغسطس 2026

**المعدّ:** Manus AI
**قرار التدقيق:** صالح للرفع إلى فرع `main` بعد التحقق المحلي؛ لا يُعد ذلك بديلاً عن مرور بوابات GitHub أو التحقق النهائي من النطاق الإنتاجي.

## 1. الملخص التنفيذي

أُجري هذا التدقيق بهدف تحويل `frontend-v3` إلى واجهة أقرب إلى تطبيق الهاتف، مع الحفاظ على تجربة سطح المكتب، وضبط حدود PWA بحيث لا تُخزّن بيانات API السريرية أو جلسات المستخدم في Service Worker. شمل العمل تجربة الدخول، وضع العرض التجريبي المعزول، لوحة التحكم، القائمة الجانبية، التنقل السفلي للهاتف، النوافذ الحوارية، المساعد الداخلي، الإشعارات، RTL، ومسارات البناء والاختبار.

كانت النتيجة الأساسية أن مشاكل العرض عند الشاشات الصغيرة عولجت دون اللجوء إلى إخفاء المحتوى أو تقليصه بصورة غير قابلة للاستخدام. أضيف تنقل سفلي مناسب للمس، وأصبح الـ drawer المغلق غير مشارك في تخطيط الصفحة، وأعيد بناء `Dialog` مع إدارة تركيز قابلة للوصول، كما أزيلت قاعدة التخزين المؤقت لطلبات API من إعداد PWA. بعد الإصلاحات، نجحت اختبارات الواجهة والوحدات وE2E وفحص التبعيات المحلي، ولم يظهر overflow أفقي في مصفوفة المقاسات المختبرة.

> **ملاحظة أمنية مهمة:** هذا التقرير لا يدّعي أن CodeQL أصبح صفراً. وفق الحالة الموروثة من لوحة المستودع، ما زالت هناك تنبيهات تاريخية مفتوحة تحتاج معالجة أو إغلاقاً موثقاً alert-by-alert. أما Dependabot المحلي/الموروث فحالته الموثقة هي صفر تنبيهات مفتوحة.

## 2. نطاق التدقيق وحدوده

ركز التدقيق على طبقة `frontend-v3` والملفات التي تؤثر مباشرة في shell المحمول وPWA. لم يُجرَ في هذه المرحلة اختبار اختراق هجومي على مستخدمين أو بيانات إنتاجية، ولم تُخزّن بيانات سريرية حقيقية في الاختبارات. تشغيل E2E المحلي استخدم خادم Vite وحده؛ لذلك ظهرت رسائل proxy من نوع `ECONNREFUSED` لواجهات backend غير المشغلة، لكن الاختبارات صممت بحيث تتحقق من حالات الفشل الآمن ولا تعتبر غياب API المحلي نجاحاً للوصول إلى بيانات سريرية.

| المجال | داخل النطاق | خارج النطاق في هذا التقرير |
|---|---|---|
| التخطيط المتجاوب | 320–1440px، overflow، drawer، bottom navigation | قياسات أجهزة فعلية متنوعة غير متاحة في sandbox |
| الدخول والعرض التجريبي | تدفق المواطن والمؤسسة ووضع Demo المعزول | إثبات صلاحية حساب إنتاجي أو جلسة مستخدم حقيقية |
| PWA | manifest، Workbox runtime caching، safe area | مراجعة متاجر التطبيقات أو توقيع الحزم |
| Accessibility | Dialog، Escape، focus trap، focus restore، ARIA | تدقيق شامل لكل مكونات WCAG في المنتج |
| الأمن | عدم تخزين API السريري في cache، npm audit | إغلاق جميع تنبيهات CodeQL التاريخية تلقائياً |

## 3. خط الأساس قبل المعالجة

### 3.1 مشاكل الهاتف والتخطيط

كان الـ dashboard يتجاوز عرض viewport في المقاسات الصغيرة، خصوصاً بين 320 و390 بكسل. السبب الجذري كان أن القائمة الجانبية المغلقة بقيت مؤثرة في التخطيط رغم عدم ظهورها بصرياً، ما أدى إلى مساحة أفقية إضافية وظهور canvas أعرض من الشاشة. كما لم يكن هناك شريط تنقل سفلي مخصص للهاتف، فكان المستخدم يعتمد على رأس الصفحة والقائمة الجانبية للوصول إلى المسارات الرئيسية.

### 3.2 تجربة الدخول

كانت صفحة الدخول تعرض مساحة العلامة التجارية الزخرفية على الهاتف مع نموذج الدخول، وهو ما أطال التدفق ونافس المحتوى الوظيفي على المساحة العمودية. عولج ذلك بتجربة form-first في الهاتف، مع إبقاء المواطن والمؤسسة ووضع العرض التجريبي واضحين وقابلين للوصول.

### 3.3 النوافذ الحوارية والعناصر العائمة

كان `Dialog` يحتاج إلى تقوية في إدارة التركيز، والاستعادة بعد الإغلاق، والإغلاق بواسطة `Escape`، وخصائص ARIA، ومنع تسرّب التفاعل إلى الصفحة الخلفية. كما كان من الضروري رفع موضع `GuideAssistant` و`ToastContainer` فوق مساحة شريط التنقل السفلي، مع احترام safe-area في الأجهزة ذات الحواف أو المؤشرات المنزلية.

### 3.4 PWA والتخزين المؤقت

كانت إعدادات PWA تحتوي قاعدة runtime caching لطلبات API، بما في ذلك استجابات قد تكون سريرية أو مرتبطة بجلسة المستخدم. تخزين هذا النوع من الاستجابات لمدة طويلة في Service Worker غير مناسب لمنصة صحية وطنية؛ لذلك أزيلت القاعدة وأبقي التخزين المؤقت موجهاً للأصول الثابتة فقط. كما كان manifest يشير إلى لقطة شاشة غير موجودة، وتمت إزالة الإشارة المكسورة.

## 4. المعالجة المنفذة

| الملف أو المكون | المعالجة | الأثر |
|---|---|---|
| `frontend-v3/src/layouts/Sidebar.tsx` | إضافة `visibility: hidden` و`pointer-events: none` عند إغلاق drawer على الهاتف | إزالة تأثير drawer المغلق من التخطيط والتفاعل ومنع overflow |
| `frontend-v3/src/layouts/DashboardLayout.tsx` | إضافة `MobileBottomNav`، و`overflow-x-clip`، و`min-h-[100dvh]`، وpadding سفلي يحترم safe-area | shell أقرب لتطبيق الهاتف ومنع تغطية المحتوى بالعناصر الثابتة |
| `frontend-v3/src/components/navigation/MobileBottomNav.tsx` | مكوّن جديد بخمسة مسارات role-aware ومخفي من breakpoint `md` فأعلى | وصول سريع للمسارات الرئيسية مع أهداف لمس مناسبة |
| `frontend-v3/src/pages/auth/LoginPage.tsx` | إخفاء اللوحة الزخرفية عند `lg` فأقل | تدفق دخول form-first على الهاتف |
| `frontend-v3/src/components/ui/Dialog.tsx` | focus trap، focus restore، Escape، `role="dialog"`، `aria-modal`، containment، safe-area | تحسين قابلية الوصول وسلامة التفاعل في الحوار |
| `frontend-v3/src/components/guide/GuideAssistant.tsx` | رفع الموضع فوق bottom navigation مع safe-area offset | منع المساعد من حجب شريط التنقل أو المحتوى |
| `frontend-v3/src/components/shared/ToastContainer.tsx` | رفع موضع التنبيهات وإضافة أهداف لمس 44px و`aria-label` للإغلاق | تحسين القراءة والتفاعل على الهاتف |
| `frontend-v3/src/styles/index.css` | `overflow-x: clip`، `100dvh`، `touch-action: manipulation`، `color-scheme`، focus-visible ring | سلوك متجاوب أكثر ثباتاً وتحسين لوحة المفاتيح واللمس |
| `frontend-v3/vite.config.ts` | إزالة API runtime cache وإشارة screenshot المفقودة | منع cache لبيانات API وتقليل أخطاء manifest |
| `frontend-v3/public/manifest.webmanifest` | إزالة `screenshot-desktop.png` غير الموجودة | manifest متسق مع الأصول الفعلية |
| `frontend-v3/eslint.config.js` و`.gitignore` | تجاهل `dev-dist` الناتج عن Workbox | منع فشل lint بسبب ملفات مولدة لا تُراجع كمصدر |
| `frontend-v3/playwright.config.ts` | دعم `PLAYWRIGHT_CHROMIUM_EXECUTABLE` | تشغيل E2E محلياً باستخدام Chromium النظامي عند غياب browser bundle |
| `frontend-v3/e2e/mobile-layout.spec.ts` | اختبار 320px و390px وdesktop، overflow، bottom nav، فتح وإغلاق drawer | حماية الانحدار في shell المحمول |

## 5. ضمانات وضع العرض التجريبي

يحافظ `frontend-v3` على وضع Demo معزول يعتمد على `sessionStorage` ولا يستخدم بيانات سريرية حقيقية. دخول Demo لا ينبغي أن يمنح جلسة backend حقيقية أو يمرر رموزاً إلى واجهات الإنتاج. كما أن إزالة runtime caching لطلبات `/api/` تمنع Service Worker من الاحتفاظ باستجابات API الحساسة خارج دورة الطلب المعتادة. هذه الضمانات لا تلغي ضرورة استمرار فرض العزل في backend، ولذلك يجب أن تظل صلاحيات الخادم والتحقق من session وRBAC هي مصدر القرار النهائي.

## 6. أدلة التحقق

| الفحص | النتيجة | الدليل أو الأمر |
|---|---:|---|
| TypeScript typecheck | ناجح | `npm run typecheck` |
| ESLint | ناجح، 0 أخطاء و0 تحذيرات | `npm run lint` |
| اختبارات الوحدة | 34 ناجحة | `npm run test -- --run` |
| Mobile regression E2E | 3 ناجحة | `e2e/mobile-layout.spec.ts` عند 320 و390 وdesktop |
| Full Playwright E2E | 44 ناجحة | `npm run test:e2e -- --project=chromium` |
| npm audit | 0 vulnerabilities | `npm audit --audit-level=high` |
| Production build | ناجح | `npm run build` |
| فحص manifest المولد | ناجح | لا توجد إشارة screenshot مفقودة |
| فحص Service Worker | ناجح | لا توجد قاعدة `api-cache` أو `NetworkFirst` لطلبات `/api/` |
| overflow matrix | ناجح | 0 overflow عند 320، 360، 375، 390، 412، 430، 768، 1024، 1280، 1440px |

اختبار E2E الكامل سجّل `44 passed` خلال 33.4 ثانية. رسائل `ECONNREFUSED` التي ظهرت أثناء التشغيل تخص proxy إلى endpoints backend محلية غير مشغلة، ولم تمنع الاختبارات من اجتياز حالات الأمان الانتقالية. يجب عدم تفسير هذه الرسائل على أنها فحص لصحة backend أو دليلاً على توفر API الإنتاجي.

## 7. الأدلة البصرية

| اللقطة | الدلالة |
|---|---|
| `/tmp/gula-mobile-audit/login-320x568.png` | صفحة دخول form-first عند 320px، مع فصل المواطن والمؤسسة وظهور Demo في تدفق قابل للاستخدام |
| `/tmp/gula-mobile-audit/dashboard-320x568.png` | Dashboard بعرض viewport، شريط تنقل سفلي بخمسة مسارات، ومساعد فوق منطقة التنقل |

تُرفق هذه اللقطات مع تسليم المهمة إن احتاج المراجع إلى فحص بصري مستقل. أما المصدر القابل لإعادة الإنتاج فهو اختبار Playwright وملفات `frontend-v3` نفسها.

## 8. توصيات ما بعد الإصدار

أوصي بتحويل الجداول السريرية الكبيرة إلى بطاقات أو صفوف قابلة للتمرير الأفقي المنضبط على الهاتف، مع الحفاظ على أسماء الحقول المهمة وعدم إخفاء قيمة سريرية دون مؤشر واضح. كما ينبغي إضافة اختبارات E2E تغطي orientation portrait/landscape، safe-area حقيقي، keyboard navigation في كل dialogs، وفشل الشبكة أثناء submit مع idempotency وعدم تكرار الأثر.

ينبغي أيضاً إضافة اختبار تكاملي يشغل backend staging مع frontend-v3 بدلاً من الاعتماد على proxy الفاشل محلياً، والتحقق من أن Demo لا يستطيع الوصول إلى endpoint حقيقي حتى مع وجود cookie أو query parameter غير متوقع. وفي بيئة CI يجب حفظ artifacts الخاصة بـPlaywright وbuild manifest وService Worker للتحقيق اللاحق.

أما بوابة CodeQL، فالمعالجة النهائية لا تكتمل إلا بعد مراجعة التنبيهات التاريخية المفتوحة واحداً واحداً. الإصلاح البرمجي وحده لا يثبت أن لوحة GitHub أغلقت التنبيه؛ يجب استخدام سبب إغلاق موثق فقط عندما يكون finding غير قابل للتطبيق أو test-only أو false positive، مع تجنب dismiss العشوائي. كذلك يجب إعادة فحص Scorecard findings الخاصة بـToken-Permissions وBinary-Artifacts وCode-Review بعد رفع commit الجديد.

## 9. قرار التسليم

من ناحية `frontend-v3`، التغييرات جاهزة للـcommit والرفع إلى `main`: الفحوص المحلية ناجحة، regression المحمول ناجح، PWA لم يعد يخزن API runtime، وواجهة الهاتف أصبحت قابلة للاستخدام دون overflow. الخطوة التشغيلية التالية هي رفع الملفات الموثقة وتشغيل CI على GitHub، ثم الانتظار حتى تمر بوابات CI/CD الفعلية قبل اعتبار الإصدار مرشحاً للنشر. بعد ذلك يجب فحص النطاقين `https://www.gula-platform.org/` و`https://gula-platform.org/` للتأكد من أن التوزيع الفعلي يشير إلى build الجديد، لا إلى cache أو artifact قديم.

## References

[1]: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/env "MDN: env() CSS function and safe-area environment variables"

[2]: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/ "WAI-ARIA Authoring Practices: Dialog (Modal) Pattern"

[3]: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API "MDN: Service Worker API"

[4]: https://developer.mozilla.org/en-US/docs/Web/API/Cache "MDN: Cache Web API"
