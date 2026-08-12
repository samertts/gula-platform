# GULA Citizen Authorization

كل Citizen API يتحقق من authenticated account، current workspace، identity level، relationship إلى citizen/patient، permission، resource ownership، policy، consent/delegation، وpurpose عند اللزوم. لا يعتمد الخادم على `patient_id` أو `citizen_id` أو role أو organization القادم من العميل.

العلاقات في `niam_citizen_relationships` تحمل type وscope وvalidity وstatus وverification وrevocation وaudit. `self` لا يمنح تلقائياً وصولاً إلى كل patient records، وguardian/delegate لا يساوي unrestricted access. الكتابة تحتاج `resource:write` صريحة؛ scope المفقود يُرفض.

تُعاد 401 للجلسة غير الصالحة، و403 للسياق المصادق غير المصرح، و404 عندما تفرض سياسة عدم كشف وجود المورد ذلك. كل denial والنجاح يسجلان audit reason code دون PHI غير اللازم. Negative tests تشمل cross-citizen، ambiguous self context، expired/revoked links، privilege escalation، workspace switching، وtenant isolation.
