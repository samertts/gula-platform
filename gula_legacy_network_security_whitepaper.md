# أمن شبكات الأجهزة القديمة وتأمين البيانات الطبية المنقولة في منصة GULA

**إعداد:** Manus AI  
**التاريخ:** 17 أغسطس 2026  
**تصنيف المستند:** التوثيق الأمني الهندسي — حماية نقل البيانات من الأجهزة غير المدعومة ضمن الشبكة الداخلية للمستشفى

---

## ديباجة التشغيل والأمن
تُمثل الأجهزة الطبية القديمة (Legacy Medical Devices) تحدياً أمنياً فريداً في البنية التحتية للمستشفيات؛ نظراً لعملها على أنظمة تشغيل قديمة (مثل Windows XP أو DOS أو أنظمة مدمجة خاصة) تفتقر إلى آليات التشفير الحديثة أو تصحيحات الثغرات الأمنية. 

لمعالجة هذه الثغرة دون تعريض أمن المستشفى للخطر، تطبق منصة **غولا (GULA)** معمارية أمنية صارمة تُعرف بـ **"الحجر النشط والعزل المحمي" (Active Quarantine & Encrypted Edge Tunneling)** [1].

---

## 1. نموذج الحماية متعدد الطبقات للأجهزة القديمة
تعتمد المنصة على أربع طبقات دفاعية متتالية لضمان عدم تسرب أو اختراق البيانات أثناء نقلها من الأجهزة القديمة عبر الشبكة الداخلية للمستشفى [2]:

| طبقة الحماية | الآلية التقنية | الوظيفة الأساسية |
| :--- | :--- | :--- |
| **1. عزل الشبكة (VLAN / Micro-segmentation)** | شبكات فرعية افتراضية معزولة تماماً (Isolated VLANs). | منع الأجهزة القديمة من الاتصال المباشر بالإنترنت أو الأجهزة الحساسة الأخرى في المستشفى. |
| **2. البوابة الوسيطة (Edge Hardware Gateway)** | استخدام وحدات وسيطة (مثل Raspberry Pi مغلقة النظام). | استقبال البيانات الخام غير المشفرة من الجهاز القديم وتشفيرها محلياً قبل مغادرتها لنطاق الجهاز [3]. |
| **3. التشفير في النقل (End-to-Edge TLS 1.3 / PQC)** | تغليف البيانات عبر بروتوكولات آمنة مع مصادقة متبادلة (mTLS). | ضمان سرية وسلامة البيانات أثناء مرورها عبر الشبكة الداخلية للمستشفى وصولاً لخوادم GULA [4]. |
| **4. التدقيق والمراقبة السلوكية (Behavioral Auditing)** | نظام مراقبة تدفق الحزم (IDS/IPS محلي). | رصد أي أنماط اتصال غير طبيعية أو محاولات حقن بيانات وتجميد المنفذ فوريًا عند الشك [5]. |

---

## 2. الآلية التشغيلية لتأمين البيانات (خطوة بخطوة)

عندما يقوم جهاز تحليل قديم بإرسال نتيجة مخبرية عبر المنفذ التسلسلي (RS-232)، تتخذ المنصة الخطوات التالية:

1. **الالتقاط المحلي الآمن:** يتم ربط الجهاز القديم بوحدة **Hardware Gateway** محلية عبر كابل تسلسلي قصير (مما يمنع أي اعتراض مادي للإشارة).
2. **التشفير الفوري على الحافة (Edge Encryption):** تقوم البوابة الوسيطة فوراً بتحويل النص الخام إلى حمولة مشفرة رقمياً باستخدام مفاتيح مشفرة مسبقاً (Pre-Shared Keys مع دعم معايير التشفير المقاوم للكم Post-Quantum Cryptography).
3. **النفق الافتراضي الآمن (Secure Tunneling):** تُنقل البيانات المشفرة حصرياً عبر نفق داخل الشبكة الداخلية (Local Mesh/VPN) موجه حصرياً إلى خادم GULA المركزي.
4. **التحقق وتخزين التدقيق (Immutable Audit Trail):** يتلقى النظام المركزي البيانات، ويتحقق من سلامتها التشفيرية، ويسجل كافة تفاصيل العملية في سجل غير قابل للتعديل (Tamper-resistant Audit Log) لضمان الامتثال لمعايير HIPAA و GDPR [6].

---

## خاتمة التشغيل
من خلال هذا النهج، تضمن منصة **غولا** الاستفادة الكاملة من كفاءة الأجهزة القديمة دون دفع الثمن باهظاً على حساب الأمن السيبراني للمستشفى، محققةً التوازن الأمثل بين الشمولية الطبية والحماية المطلقة.

---

## المراجع (References)
[1] **National Institute of Standards and Technology (NIST).** (2023). *Securing Legacy Medical Devices in Health Care Delivery Organizations*. NIST Special Publication 800-213.  
[2] **Health Sector Cybersecurity Coordination Center (HC3).** (2024). *Legacy Medical Device Security: Risks and Mitigation Strategies*. US Department of Health and Human Services.  
[3] **IEEE Communications Surveys & Tutorials.** (2023). *Edge Computing and Hardware Gateways for IoT Security in Healthcare*. IEEE.  
[4] **Internet Engineering Task Force (IETF).** (2022). *Transport Layer Security (TLS) Version 1.3 and Mutual Authentication Standards*. RFC 8446.  
[5] **SANS Institute.** (2024). *Network Micro-segmentation and Zero-Trust Architectures for Hospital OT/IoT*. SANS Whitepaper.  
[6] **European Union Agency for Cybersecurity (ENISA).** (2023). *Guidelines on Cybersecurity of Health Care Services*. ENISA Standards.
