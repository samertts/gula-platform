# GitHub Actions execution block — evidence

في run `32158462896` الخاص بـPR #239، عرضت صفحة GitHub أن حالة التشغيل `Failure` ومدته ست ثوانٍ، وأن job `Expo SDK 54 Typecheck and Unit Tests` لم يبدأ أي خطوة. نص annotation الظاهر هو: “The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings”. لذلك فإن حالات failure المتكررة في PRs الحالية ليست نتيجة فشل typecheck أو tests؛ GitHub يمنع إنشاء runner قبل بدء الخطوات بسبب إعدادات الفوترة/حد الإنفاق للحساب أو المؤسسة.

**Run URL:** https://github.com/samertts/gula-platform/actions/runs/32158462896
**Observed attempt:** #2، بتاريخ 2026-08-18.

## PR #241 hotfix

Run `32160563846` على commit `b11916f6` أعاد GitHub UI الحالة Failure. Annotation الرسمية كانت: **"The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings."** وظيفة Syntax Gate استغرقت 5 ثوانٍ بلا خطوات، وبقية الوظائف (`Data Preservation Gate`, `Migration Check`, `Lint`, `Backend Tests`, `Security Scan`) كانت skipped وبلا خطوات. هذا يؤكد أن فحوص hotfix المحلية ليست سبب الفشل، وأن الدمج الآمن ينتظر معالجة Billing & plans في GitHub.

Run URL: https://github.com/samertts/gula-platform/actions/runs/32160563846
PR URL: https://github.com/samertts/gula-platform/pull/241

## Latest PR #241 head verification

Run `32160878437` الخاص بـFormatting Check على head `0cd4461bf4979310df2b1c93b45b0a94004457e8` فشل قبل التنفيذ. GitHub UI عرض الوظيفتين `Ruff Format (Python)` و`Prettier (TypeScript/JSON/MD)` بحالة failure ومدد 3 و5 ثوانٍ، لكن annotation لكلتيهما كانت: **"The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings."** لا توجد أخطاء formatting كودية حتى الآن.

Run URL: https://github.com/samertts/gula-platform/actions/runs/32160878437

## Latest security-hardening head

Run `32218061732` لـCI Pipeline على head `f16f83ec86eeebb394144d6002ab6a5bcdc06cb7` بتاريخ 19 أغسطس 2026 فشل خلال 4 ثوانٍ. ظهرت وظيفة Syntax Gate فقط لمدة 3 ثوانٍ، بينما بقية الوظائف لم تبدأ عملياً. Annotation الرسمية بقيت: **"The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings."** لا توجد إشارة إلى فشل في hardening أو الاختبارات.

Run URL: https://github.com/samertts/gula-platform/actions/runs/32218061732

## Mobile Expo workflow on latest head

Run `32218123745` لـMobile Expo Speech Quality على head `53dbd95e8e2e60409bcfe096cb35837825d4fa86` فشل خلال 4 ثوانٍ. وظيفة `Expo SDK 54 Typecheck and Unit Tests` لم تبدأ أي خطوة، وannotation GitHub نفسها تشير إلى فشل دفعات الحساب أو الحاجة لرفع spending limit.

Run URL: https://github.com/samertts/gula-platform/actions/runs/32218123745
