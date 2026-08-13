# TLS Pinning Evidence

تم التحقق خارجياً في 2026-08-13 من شهادة `api.gula-platform.org` عبر TLS مع SNI.

| العنصر | القيمة |
|---|---|
| Subject | `CN=gula-platform.org` |
| SAN | `*.gula-platform.org`, `gula-platform.org` |
| Issuer | Let's Encrypt YE1 |
| Validity observed | 2026-07-08 إلى 2026-10-06 بتوقيت GMT |
| Public-key algorithm | ECDSA P-256 (`id-ecPublicKey`, `prime256v1`) |
| SPKI pin | `sha256/g9F05XEMwoJmxPy/otHWQ4jyLsg5jcPWyh4PYBrOEM0=` |

القيمة أعلاه ليست مفتاحاً سرياً؛ هي بصمة عامة لمفتاح الشهادة وتستخدم فقط للتحقق من certificate pinning. يجب تحديثها مع بصمة احتياطية موثقة قبل تجديد الشهادة أو تغيير سلسلة CA، ثم إجراء اختبار release على Android وiOS وdesktop.
