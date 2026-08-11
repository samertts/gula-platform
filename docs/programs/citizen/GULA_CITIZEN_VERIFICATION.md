# GULA Citizen Verification

تستخدم المنصة verification levels تدريجية: حساب غير موثق، contact verified، identity verified، Health ID linked، ثم high-assurance/regulated context عند توفر provider معتمد. لا تُجعل كل الطرق mandatory إذا كان risk-based policy يحقق الأمان، ولا تُعلن وسيلة حكومية أو biometric قبل وجود connector واعتماد قانوني وتقني.

تُدار mobile OTP وemail verification وMFA وdevice binding وpasskeys خلف abstraction قابلة لتغيير provider. لا تُخزن biometric raw data، ولا تُسجل OTP أو recovery secrets. الإجراءات عالية الحساسية مثل تغيير الهوية أو recovery أو إضافة delegate أو export تحتاج step-up.

بعد recovery أو تغيير أمني تُبطل الجلسات المعرضة، وتُرسل security notification، ويسجل القرار في audit. فشل verification لا يكشف تفاصيل تمكّن enumeration أو account takeover.
