# طبقة تعاون أنظمة الذكاء الاصطناعي في GULA

## القرار المعماري

يوجد الآن بروتوكول تنسيق مستقل عن مزود النموذج في `tools/ai_coordination/`. وهو ليس بديلاً عن `backend/app/ai/orchestrator.py`: ذلك الـOrchestrator يعالج طلبات المساعد داخل المنصة، بينما طبقة التنسيق الجديدة تحكم **تعاون أدوات التطوير** مثل Claude Code وManus وCopilot وأي وكيل آخر يعمل على المستودع.

تستخدم الطبقة SQLite محلية ومعاملات ذرية لتسجيل الوكلاء والمهام وleases ونوايا تغيير الملفات والرسائل وسجل الأحداث. لا تخزن الطبقة PHI أو الأسرار أو بيانات المرضى، ولا تمنح أي وكيل صلاحية الكتابة المباشرة إلى `main` أو الدمج التلقائي.

## دورة العمل الإلزامية

```text
register agent -> create/claim task -> declare file intent
       -> inspect current commit -> edit in own branch/worktree
       -> run tests -> send handoff with commit/evidence
       -> close intent -> human/PR review
```

إذا أعلن وكيلان نية تعديل مسارين متداخلين، يُرفض الإعلان الثاني بدلاً من overwrite. وإذا حاول وكيل claim مهمة محجوزة، يحصل على تعارض. تنتهي claims تلقائياً بعد انتهاء lease، لكن لا ينبغي اعتبار انتهاء lease دليلاً على أن الوكيل الآخر توقف؛ يجب إرسال رسالة handoff أو فحص Git قبل الاستلام.

## أمثلة تشغيل

```bash
export GULA_COORDINATION_DB=.gula/coordination.sqlite3

python -m tools.ai_coordination.cli register \
  --agent-id claude-a --provider claude --model sonnet

python -m tools.ai_coordination.cli task create \
  "Review national gateway" "Check contracts and tests" --created-by human

python -m tools.ai_coordination.cli task claim task-XXXXXXXXXXXX \
  --agent-id claude-a --lease-seconds 900

python -m tools.ai_coordination.cli intent declare task-XXXXXXXXXXXX \
  --agent-id claude-a --operation modify \
  backend/app/gateways/national_integration_gateway.py \
  backend/tests/test_national_integration_gateway.py

python -m tools.ai_coordination.cli message send \
  --sender-id claude-a --recipient-id claude-b --kind handoff \
  '{"commit":"abc123","tests":"20 passed","next":"review"}'

python -m tools.ai_coordination.cli message receive --agent-id claude-b
python -m tools.ai_coordination.cli status

# سجل التدقيق بصيغة JSON
python -m tools.ai_coordination.cli audit --limit 100

# مراقبة الحالة والأحداث كل ثانيتين؛ أوقفها بـ Ctrl-C
python -m tools.ai_coordination.cli watch --interval 2
```

## حدود مهمة

هذه الطبقة تنسق الرسائل والملكية، لكنها لا تجعل حسابي Claude يتحدثان تلقائياً عبر واجهة Claude أو تمنحهما صلاحيات GitHub جديدة. لكي يعمل التواصل الفوري بين حسابين يجب تشغيلهما على نفس مخزن التنسيق أو إضافة adapter مصادق عليه (مثل webhook داخلي أو MCP خاص) مع إبقاء Git/PR بوابة الحقيقة. لا يُسمح بإضافة token إلى المستودع.

## الاختبار

اختبارات `tests/test_ai_coordination.py` تثبت claims المتنافسة، منع تعارض الملفات، الرسائل ذات القراءة مرة واحدة، ومنع الفروع المحمية. الاختبارات تستخدم SQLite مؤقتاً ولا تتصل بالشبكة ولا بأي حساب Claude.

أضيفت لها بوابة CI مستقلة باسم `AI Coordination Tests` وتقرير JUnit، حتى لا تعتمد سلامة بروتوكول التعاون على نجاح اختبارات المجال السريري وحدها.

يكتب `audit` الأحداث غير القابلة للتعديل في جدول `events`، بينما يعرض `watch` الحالة والنوايا النشطة والأحداث الجديدة عبر polling. هذه مراقبة لحظية عملية وليست WebSocket؛ لا توجد حالياً خدمة MCP/HTTP أو منفذ شبكة مفتوح. استخدم `GULA_COORDINATION_DB` نفسه لدى جميع الوكلاء كي يروا الحالة ذاتها.
