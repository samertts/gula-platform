# GULA Citizen Offline and Synchronization

العمل offline degraded وليس bypassاً للتفويض أو التدقيق. الحالات الظاهرة للمواطن هي ONLINE وOFFLINE وSYNCING وSYNC_ERROR، مع `LAST UPDATED` واضح لكل بيانات مخزنة. تُخزن فقط بيانات justified مثل basic account state أو appointment مختارة أو documents صراحةً للتخزين، وتُشفّر البيانات الحساسة محلياً.

لا تُجرى clinical writes offline في C1. عند إضافة writes لاحقاً ستحتاج outbox/idempotency/version/conflict resolution، وتُسمح فقط بالعمليات المعتمدة في degraded policy. لا تُعرض stale clinical data كأنها current، ولا تُستخدم cache لتوسيع scope عند تبديل profile/workspace.

تشمل الاختبارات انقطاع الشبكة، انتهاء session أثناء offline، stale result، retry/backoff، duplicate sync، conflict، recovery، ومسح cache عند revoke أو logout-all.
