# C13: تصميم احتفاظ Fail-Closed قبل الأتمتة

**الفرع:** `docs/c13-retention-fail-closed-design`
**القاعدة:** `release/clinical-safety-2026q3-rc1` عند `dfd9396275393c95e596a9b8a2416dc00956b1a6`
**الحالة:** تصميم فقط؛ لا يوجد حذف أو أرشفة تنفيذية أو schedule أو نشر في هذه الدفعة. يبقى C13 وGO **NO-GO**.

> لا يجوز تحويل مدد حفظ واردة في تقرير تحقق إلى حذف آلي ما لم يعتمدها مالك قانوني وخصوصية، مع jurisdiction وlegal hold ومسار اعتراض وإثبات قابل للمراجعة. عند غياب أي معلومة، يجب أن يفشل النظام مغلقاً بالاحتفاظ وعدم الحذف.

## ما هو موجود وما لا يكفي

| الموجود في RC1 | حدّه |
|---|---|
| `trust_retention_policies` ونماذج retention في Trust | بنية سياسة، لكن لا دليل على خريطة معتمدة تشمل فئات السجل السريري ونتائج المختبر وسجل التدقيق. |
| `apply_retention_policy()` في Document Intelligence | يكتب سياسة `standard_7y` وسجل lifecycle لتوثيق فقط؛ لا يحدد تاريخاً ملزماً ولا يطبق policy متعددة الفئات ولا ينفذ حذفاً. |
| background/scheduling platform عامة | لا توجد وصلة مثبتة إلى وظيفة احتفاظ معتمدة أو أدوات حماية من الحذف الخاطئ. |
| تقرير التحقق C13 | يذكر مدد 25/10/7 سنوات، لكنه ليس بديلاً عن مصدر قانوني versioned قابل للاعتماد. |

## الضابط المقترح: مراقبة بلا تدمير

المرحلة التالية الآمنة هي **Retention Eligibility Monitor** تقرأ البيانات الوصفية فقط، ولا تعدل السجل السريري ولا تحذف أو تؤرشف الملفات. تقبل مدخلاً من registry معتمد، وتحسب `not_before` و`policy_version` وسبب التصنيف، ثم تصدر تقريراً مجمعاً للمختصين يبين العناصر غير المصنفة أو المعلقة أو التي تحتاج قراراً. لا يحتوي التقرير PHI أو محتوى سريرياً.

| شرط الإدخال | سلوك Fail-Closed |
|---|---|
| فئة سجل غير معروفة | تسجل استثناء امتثال وتحفظ السجل. |
| policy غير فعالة أو غير موقعة | تحفظ السجل ولا تحسب eligibility. |
| legal hold أو litigation hold | تعطل كل انتقال إلى archive/delete. |
| تضارب jurisdiction أو tenant | تحفظ السجل وترفع حالة للمراجعة. |
| فقدان audit lineage أو checksum | تمنع أي معالجة لاحقة وتطلب إصلاح الدليل. |

## المتطلبات السابقة لأي تنفيذ مؤتمت

1. اعتماد قانوني/خصوصية مكتوب لمصفوفة: فئة السجل، jurisdiction، المدة، البداية، legal basis، الاستثناءات، policy version، ومالك الاستثناء.
2. نمذجة append-only لسجلات القرار والـhold وعمليات archive أو disposal؛ لا overwrite ولا soft-delete بلا audit.
3. تعريف archive غير قابل للتعديل، تشفير، مفاتيح محتفظ بها، checksum، وrestore drill؛ لا يعني archive حذفاً من دون قرار مستقل.
4. عزل tenant في كل query، وتقارير مجمعة خالية من PHI، وصلاحيات فصل واجب بين policy author والمراجع والمنفذ.
5. UAT تركيبية تشمل تقادم التاريخ، policy change، hold، الاسترجاع، tenant cross-access، إعادة تشغيل وعدم التكرار، وrollback.
6. نشر خارجي مراقب بعد اعتماد التشغيل، وليس daemon أو cron في sandbox أو API process.

## تنفيذ مرفوض في هذه الدفعة

لم يضف هذا الفرع `DELETE`, `purge`, job مجدول، migration، أو تغيير مدة سياسة. لا يُسمح بتشغيل `apply_retention_policy()` كمحرك حذف؛ مساره الحالي لا يثبت ذلك ولا يغطي الفئات الملزمة. كما لا يحوّل التصميم تقرير C13 إلى حالة امتثال أو GO.

## المراجع

[1] [تقرير التحقق الدستوري: C13](constitution/CONSTITUTION-VALIDATION-REPORT.md)

[2] [نموذج Trust للاحتفاظ](../backend/app/trust/models.py)

[3] [خدمة Document Intelligence](../backend/app/document_intelligence/infrastructure/services.py)
