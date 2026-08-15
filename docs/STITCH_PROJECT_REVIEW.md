# مراجعة مشروع Stitch الحالي لـGULA

## الحالة

المشروع متاح في Stitch تحت العنوان `GULA Medical Operations Dashboard`، والرابط الحالي هو:

<https://stitch.withgoogle.com/projects/13295883883801481875>

تمت مراجعته بعد تسجيل الدخول إلى حساب المستخدم. يحتوي المشروع على Canvas واسع ومجموعة كبيرة من الشاشات المولدة. هذا المستند لا يعتبر موافقة نهائية على كل شاشة؛ بل يحدد ما ظهر في المشروع وكيف ستتم مراجعته قبل إدخال أي جزء إلى GULA.

## الشاشات المرئية

| المجموعة | الشاشات المرئية أو القريبة من نطاق GULA | قرار المراجعة الأولي |
|---|---|---|
| الأساس | GULA Foundations & UI Kit، Final Design Tokens & Specs | مرجع الهوية والمكونات بعد مطابقة tokens مع GULA |
| الوصول العام | GULA Public Landing Page، Select Account Type، GULA Login Screen، Account Locked & Recovery Path | أولوية UX-1؛ يجب إبقاء التسجيل المواطن غير مفعّل في المرحلة الحالية |
| المواطن | Citizen Home Dashboard، Secure Health Preferences Flow، GULA Settings Home - Mobile | مراجعة الخصوصية والحدود قبل التنفيذ؛ لا بيانات سريرية أو وطنية فعلية |
| المؤسسة | Multi-Organization Workspace Switcher، University & Education Hierarchy View، Security & Device Management | أولوية UX-2؛ يجب إبقاء تبديل المساحة server-authoritative |
| التشغيل | Radiology Workspace Dashboard - Desktop، Healthcare Professional Dashboard - Desktop، GULA LAB dashboards، Financial Dashboard - Desktop View | لا تُنفذ تلقائيًا؛ تتطلب تحديد scope وبيانات typed من backend |
| السجلات والحوكمة | Accessibility Data Model & Security Specs، Implementation Readiness & Final Report | مرجع توثيقي، ويجب تدقيق أي ادعاء قانوني أو أمني قبل اعتماده |
| التفاصيل المتخصصة | Patient Clinical Timeline - Mobile، Lab Result Details، Service Checkout - Mobile View | خارج دفعة الواجهة الأولى؛ لا تُفعّل تدفقات سريرية أو دفع في P4 |

## حواجز الاعتماد

تصميم Stitch هو فرضية بصرية وليس مصدر صلاحيات أو بيانات. أي مكوّن يُنقل إلى GULA يجب أن يرتبط بمكوّن React قائم أو PR مستقل، مع حالات typed للتحميل والفراغ والخطأ ومنع الوصول والعمل غير المتصل. لا يجوز إدخال أسماء مواطنين أو مرضى أو جهات حكومية حقيقية أو بيانات سريرية مصطنعة تبدو واقعية.

يجب أن تبقى حالة التحقق منفصلة عن نوع الجهة، وأن تبقى العضوية منفصلة عن الدور والصلاحية والاستحقاق ومساحة العمل. لا يجوز أن توحي الألوان أو بطاقات الإحصاءات بأن جهة ما موثقة أو مخولة لمجرد اسمها. أي تبديل مساحة عمل أو تغيير صلاحية أو انتقال سريري يجب أن يبقى قرارًا server-authoritative، مع الحفاظ على audit trail وعدم استخدام optimistic success.

## ترتيب التنفيذ المقترح

تبدأ الدفعة الأولى من شاشة الدخول واختيار المسار، ثم لوحة التحكم ومساحة العمل، ثم شاشة المواطن الأساسية، وبعدها شاشة المؤسسة وتبديل المساحة. تؤجل لوحات الأشعة والنتائج السريرية والدفع وأي تكاملات خارجية إلى مراحل منفصلة ومراجعة مستقلة. لا يبدأ P5 نتيجة هذا التصميم، ولا يغيّر هذا المسار حالة P4 أو بوابات الدمج والنشر.

## ملاحظة التصدير

تم فحص واجهة التصدير في Stitch، ولم يظهر ملف قابل للتنزيل في مجلد Downloads بعد التفاعل. لذلك يعتمد المسار الحالي على مراجعة المشروع المرئي، و`DESIGN.md`، وموجّهات Stitch، ثم تنفيذ نسخة GULA الأصلية عبر PRs واختباراتها بدل إدخال كود مولد مباشرة.
