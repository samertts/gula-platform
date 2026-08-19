# معمارية ربط الأجهزة القابلة للارتداء (Wearables) بمحرك القواعد في GULA

يتطلب ربط الأجهزة القابلة للارتداء (مثل Apple Watch, Fitbit, Garmin) مع محرك القواعد السريرية في GULA بناء طبقة وسيطة تتعامل مع البيانات غير المهيكلة وتحولها إلى أحداث سريرية لحظية.

---

## 1. هيكلية تدفق البيانات (Data Flow Architecture)

يمر تدفق البيانات بأربع مراحل أساسية لضمان الدقة والسرعة:

1.  **الاستقبال (Ingestion):** عبر واجهات برمجة التطبيقات (APIs) أو Webhooks من سحابة الشركة المصنعة (Cloud-to-Cloud) أو مباشرة من تطبيق الجوال (Mobile SDK).
2.  **التوحيد (Normalization):** تحويل البيانات المتنوعة إلى تنسيق `DeviceResult` الموحد في GULA.
3.  **البث (Streaming):** إرسال البيانات الموحدة إلى `EventBus` تحت حدث `VITAL_SIGNS_UPDATED`.
4.  **المعالجة (Processing):** يلتقط محرك القواعد السريرية الحدث ويقوم بتقييمه فورًا.

---

## 2. المكونات التقنية المطلوبة

### أ. محول الأجهزة السحابي (Cloud Device Adapter)
يجب توسيع `DeviceAdapter` الحالي ليدعم البيانات القادمة من JSON بدلاً من البايتات الخام (Raw Bytes) التقليدية:

```python
class WearableAdapter(DeviceAdapter):
    def parse_json(self, payload: dict) -> list[DeviceResult]:
        # تحويل بيانات Fitbit/Apple إلى DeviceResult
        return [DeviceResult(
            device_id=payload['source_id'],
            patient_id=payload['user_id'],
            test_code="HEART_RATE",
            result_value=str(payload['value']),
            unit="bpm",
            timestamp=payload['time']
        )]
```

### ب. طبقة الاستقبال (Ingestion Layer)
إنشاء نقطة نهاية (Endpoint) تستقبل الـ Webhooks من منصات مثل **Terra API** أو **Rhealth** (التي تجمع بيانات معظم الأجهزة القابلة للارتداء في واجهة واحدة):

```python
@app.post("/ingest/wearables/{provider}")
async def receive_wearable_data(provider: str, data: dict):
    adapter = adapter_registry.get(provider)
    results = adapter.parse_json(data)
    for res in results:
        events.emit("VITAL_SIGNS_UPDATED", payload=res.__dict__)
```

---

## 3. ربط البيانات بمحرك القواعد (The Clinical Link)

بمجرد وصول البيانات إلى `EventBus` في GULA، يتم تفعيل محرك القواعد كالتالي:

| نوع البيانات | القاعدة السريرية (مثال) | الإجراء (Action) |
| :--- | :--- | :--- |
| **نبضات القلب (HR)** | إذا تجاوزت 120 نبضة/دقيقة أثناء الراحة. | تنبيه المريض + إخطار الممرض المناوب. |
| **أكسجين الدم (SpO2)** | إذا انخفض عن 92% لمدة تزيد عن 5 دقائق. | إنشاء حالة طوارئ (Emergency Ticket). |
| **جودة النوم** | إذا انخفضت الكفاءة عن 50% لثلاث ليالٍ متتالية. | جدولة موعد استشاري للصحة النفسية/النوم. |

---

## 4. التحديات وكيفية معالجتها في GULA

1.  **حجم البيانات (Data Volume):** الأجهزة القابلة للارتداء ترسل آلاف النقاط.
    *   *الحل:* استخدام **"تصفية الحافة" (Edge Filtering)**؛ لا نرسل كل نبضة قلب، بل نرسل فقط المتوسطات أو القراءات التي تتجاوز حدودًا معينة.
2.  **دقة البيانات:** الأجهزة الاستهلاكية ليست دائمًا بدقة الأجهزة الطبية.
    *   *الحل:* وسم البيانات في GULA بـ `source_type="CONSUMER_WEARABLE"` ليعرف الطبيب مصدر المعلومة ويتم تقييمها بحذر.
3.  **استهلاك البطارية:** المزامنة اللحظية تستهلك بطارية الهاتف.
    *   *الحل:* المزامنة على دفعات (Batching) كل 15 دقيقة، مع استثناء الحالات الطارئة التي تتطلب بثًا فوريًا.

---

## 5. التوصية النهائية للتنفيذ

ابدأ بدمج **Apple HealthKit** و **Google Fit** كأول مصادر للبيانات، حيث يغطيان أكثر من 80% من مستخدمي الأجهزة القابلة للارتداء. استخدم وحدة `shared/events` في GULA لتكون هي المحرك المركزي الذي يربط هذه البيانات بمحرك القواعد السريرية الذي صممناه سابقًا.
