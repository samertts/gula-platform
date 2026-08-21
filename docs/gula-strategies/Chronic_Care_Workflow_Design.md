# تصميم محرك سير العمل (Workflow Engine) لإدارة الأمراض المزمنة في GULA

يعتمد هذا التصميم على دمج تجربة **Teladoc (Livongo)** في الرعاية الاستباقية مع بنية منصة **GULA** التقنية، لتحويل النظام من مجرد مستقبل للبيانات إلى محرك ذكي يدير رحلة المريض.

---

## 1. المفهوم العام: من "التنفيذ المتسلسل" إلى "الاستجابة اللحظية"

بينما يعتمد محرك GULA الحالي (`shared/workflow/engine.py`) على خطوات متسلسلة، تتطلب إدارة الأمراض المزمنة محركًا **قائمًا على الأحداث (Event-Driven)** و**مدركًا للحالة (Stateful)**.

### المكونات الرئيسية المقترحة:
1.  **مستقبل الأحداث (Event Listener):** يراقب نتائج الأجهزة الطبية عبر `EventBus`.
2.  **محرك القواعد السريرية (Clinical Rule Engine):** يقيم البيانات بناءً على عتبات (Thresholds) محددة طبيًا.
3.  **مدير الحالة (State Manager):** يحدد مرحلة المريض (مثلاً: "مستقر"، "تحت المراقبة المكثفة"، "حالة حرجة").
4.  **منفذ الإجراءات (Action Executor):** ينفذ التدخلات (رسائل تنبيه، حجز موعد، إخطار الطبيب).

---

## 2. هيكلية سير العمل (Workflow Architecture)

نقترح إضافة فئة جديدة `ChronicCareWorkflow` تستفيد من `WorkflowEngine` الحالي ولكن بإضافة منطق "المحفزات":

```python
# تصور برمجي لتوسيع المحرك الحالي
class ChronicCareWorkflow(WorkflowInstance):
    def __init__(self, patient_id: str, condition: str):
        self.patient_id = patient_id
        self.condition = condition # e.g., "Diabetes"
        self.current_state = "STABLE"

    def on_device_data(self, data: DeviceResult):
        # 1. تقييم القواعد (Rule Evaluation)
        action_needed = self.evaluate_rules(data)

        # 2. تغيير الحالة إذا لزم الأمر
        if action_needed == "URGENT_INTERVENTION":
            self.transition_to("CRITICAL")
            self.trigger_action("ALERT_COACH")
        elif action_needed == "NUDGE":
            self.trigger_action("SEND_PATIENT_SMS", message="اشرب الماء وأعد الفحص")
```

---

## 3. اقتباس تجربة Teladoc في GULA

| ميزة Teladoc | كيفية تطبيقها في GULA | المكون التقني المسؤول |
| :--- | :--- | :--- |
| **التنبيهات اللحظية (Nudges)** | إرسال رسائل فورية للمريض عند رصد قراءة خارج النطاق. | `shared/notifications` + `shared/events` |
| **التدخل البشري الذكي** | توجيه الحالة لمدرب صحي (Coach) فقط عندما تفشل التنبيهات الآلية. | `shared/workflow` (Conditional Steps) |
| **تكامل الأجهزة (IoT)** | الربط المباشر مع أجهزة السكري والضغط. | `shared/device/adapters.py` |
| **التقارير الاتجاهية (Trends)** | تحليل البيانات على مدار أسبوع وتقديم نصائح وقائية. | `shared/ai` + `shared/metrics` |

---

## 4. نموذج سير عمل "إدارة السكري" (مثال تطبيقي)

1.  **المحفز (Trigger):** وصول قراءة سكر دم > 250 mg/dL عبر `DeviceAdapter`.
2.  **التحقق (Validation):** التأكد من أن القراءة ليست "خطأ تقني" (عبر `shared/validators`).
3.  **الإجراء الآلي (Automated Action):** إرسال تنبيه للمريض يسأله عن آخر وجبة أو شعوره بأعراض معينة.
4.  **التصعيد (Escalation):** إذا لم تنخفض القراءة خلال ساعتين، يتم إنشاء "مهمة" (Task) في لوحة تحكم الطبيب/المدرب.
5.  **التوثيق (Audit):** تسجيل كل خطوة في `shared/audit` لضمان الامتثال الطبي.

---

## 5. التوصيات التقنية للتنفيذ

-   **الاستفادة من `shared/events`:** يجب أن يكون محرك سير العمل مشتركًا دائمًا في أحداث `DEVICE_RESULT_RECEIVED`.
-   **فصل القواعد عن الكود:** تخزين القواعد السريرية (مثل نطاقات السكر) في قاعدة البيانات أو ملفات تكوين (JSON/YAML) لسهولة تحديثها من قبل الأطباء دون تغيير الكود.
-   **الاعتمادية (Reliability):** استخدام `shared/retry` لضمان وصول التنبيهات الحرجة حتى في حال فشل الشبكة المؤقت.

---
**النتيجة:** بهذا التصميم، تتحول GULA من نظام "سجل طبي" إلى "مساعد طبي نشط" يدير صحة المريض على مدار الساعة، تمامًا كما تفعل كبرى المنصات العالمية.
