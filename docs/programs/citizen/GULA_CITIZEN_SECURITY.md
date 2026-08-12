# GULA Citizen Security

الويب يستخدم HttpOnly Secure SameSite cookies مع token rotation وperm_version/revocation، والموبايل يستخدم secure storage. كل API يعتمد server-side authentication وRBAC/resource/context checks وCSRF policy حيث تنطبق. لا توجد passwordless production backdoor أو secrets في client source.

P0 security threat هو IDOR في `/citizen-platform/*/{citizen_id}`؛ C1 أضاف explicit active relationship guard وown-context `/me/*` paths، ورفض scope المفقود والـambiguous self context، وسجل access decisions. تبقى المسارات القديمة compatibility ولا تُعتبر public citizen contract.

Security Center سيعرض الأجهزة والجلسات وMFA وrecovery والأحداث الأخيرة، ويسمح revoke/sign-out-all مع session invalidation. تُطبق rate limits على login/OTP/recovery، وتُحجب raw national ID وtokens وPHI غير الضروري من logs وanalytics. Demo يستخدم DB/Redis/secrets/connectors منفصلة وsynthetic data فقط.
