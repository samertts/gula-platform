# GULA P4 Evidence Bundle — 2026-08-17

هذا المجلد يجمع **الوثائق والأدلة الآمنة القابلة للتدقيق** الناتجة عن أعمال P4 Commands 02 و03 و04 على الفرع `chore/security-ddos-hardening-clean` وPR #226. أُنشئ هذا الفهرس من أجل حفظ نتائج العمل داخل مستودع المشروع، وليس لتغيير حالة الاعتماد أو تجاوز أي SAFE_STOP.

## نطاق الحزمة

| القسم | المحتوى |
|---|---|
| Command 02 | تقرير معالجة quality debt ونتائج الاختبارات المحلية والقيود المتبقية |
| Command 03 | تقرير database/runtime hardening ونتائج Docker/compose/Alembic |
| Command 04 | تقرير authentication/IAM hardening، SAFE_STOP الخاص بمواد Android signing، وإعادة تقييم CI |
| Local verification | نتائج backend regression وtargeted security tests وchanged-files quality gate وsecret guard |
| CI evidence | جداول منزوعة القيم الحساسة لحالات GitHub Actions ومحاولات rerun، مع إبقاء الروابط العامة للـruns فقط |

## الحالة عند إنشاء الحزمة

آخر commit مرفوع إلى الفرع هو `92ae8aec0ccec4139938d63396d06f2f6cb6ff6c`. بقي PR #226 مفتوحاً وحالته `UNSTABLE`. لم يتم تنفيذ merge أو force-push أو نشر إنتاجي أو تعديل قاعدة بيانات أو تغيير أسرار خارجية.

| القرار | الحالة |
|---|---|
| P4 Command 02 | PARTIAL / موثق؛ local gates ناجحة مع بقاء legacy debt وCI blocker |
| P4 Command 03 | COMPLETE محلياً وفق التقرير، مع بقاء الأدلة الخارجية غير المنفذة حيث وردت |
| P4 Command 04 | SECURITY_BLOCKED — AUTHENTICATION_PARTIAL |
| P5 / Command 05 | P5_BLOCKED_BY_PREREQUISITE؛ لم يبدأ |

## الملفات المستبعدة عمداً

لم تُرفع ملفات `/tmp` الخام، أو ملفات البيئة، أو السجلات غير المنقاة، أو أي keystore أو signing properties أو مفاتيح أو شهادات أو كلمات مرور أو tokens أو session secrets. كما لم تُرفع ملفات virtual environments أو `node_modules` أو caches أو ملفات `__pycache__`. السبب هو أن رفع "كل شيء" حرفياً قد يعيد نشر بيانات اعتماد أو معلومات تشغيلية حساسة، وهو مخالف لمتطلبات SAFE_STOP.

تم رفع **نسخ ملخصة ومنقاة** من الأدلة بدلاً من السجلات الخام. لا تحتوي هذه النسخ على قيم سرية؛ وهي تحفظ counts وstatuses وcommit/run identifiers اللازمة للتدقيق فقط.

## ملاحظة أمنية

وجود التقرير داخل GitHub لا يعني أن Android signing incident أُغلق. ما زال مطلوباً خارجياً تدوير أو إبطال مفتاح Android production، تدوير أسرار CI، وتنفيذ history containment معتمد قبل إعادة تقييم P4. لا يجوز استخدام هذه الحزمة لإعلان PASS أو لبدء P5.

## References

[1]: https://github.com/samertts/gula-platform/pull/226 "GULA Platform PR #226"
[2]: https://github.com/samertts/gula-platform/actions "GULA Platform GitHub Actions"
