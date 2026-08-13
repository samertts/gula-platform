# مراجع خارجية للتقرير الأمني

## [1] OWASP Secrets Management Cheat Sheet
URL: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

النقاط المستخدمة: توصي OWASP بمركزة وتوحيد إدارة الأسرار، وتطبيق أقل صلاحية على من يستطيع قراءة أو تحديث الأسرار، وأتمتة إنشاء الأسرار وتدويرها، مع تقليل التعامل اليدوي معها. كما تشير إلى أن مفاتيح API وبيانات قواعد البيانات ومفاتيح IAM وSSH أمثلة على أسرار يجب حمايتها.

## [2] OWASP Session Management Cheat Sheet
URL: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

النقاط المستخدمة: تعتبر OWASP أن معرّف الجلسة يعادل مؤقتاً أقوى وسيلة مصادقة للمستخدم، وأن كشفه أو التقاطه أو التنبؤ به قد يؤدي إلى انتحال الجلسة. وتوصي باستخدام آلية جلسات مناسبة بخصائص آمنة، ومعرّفات غير ذات معنى، وتوليد عشوائي قوي، وعدم وضع معلومات حساسة داخل المعرّف.

## [3] OWASP Content Security Policy Cheat Sheet
URL: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html

النقاط المستخدمة: توضح OWASP أن CSP طبقة دفاع إضافية ضد XSS وclickjacking وتسريب المعلومات، وأن ترويسة CSP هي طريقة التسليم المفضلة ويجب إرسالها في جميع الاستجابات، لا في صفحة index فقط. كما تشرح أن connect-src يتحكم في fetch وXHR وEventSource وWebSocket، وأن السياسات الصارمة المعتمدة على nonce/hash أكثر أماناً من allowlists الواسعة.
