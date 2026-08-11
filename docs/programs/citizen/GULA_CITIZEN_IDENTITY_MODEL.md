# Citizen Identity Model

يمثل المواطن شخصاً داخل NIAM عبر `niam_persons` و`niam_identities`، بينما يمثل `national_citizens` السجل الوطني/الصحي ويمثل `national_patients` السياق السريري. لا يُساوى account بالشخص، ولا citizen بالمريض؛ كل علاقة بين هذه الكيانات يجب أن تكون صريحة ومدققة.

## Health ID

يظل Health ID مرجعاً صحياً مستقراً وopaque في الواجهات. لا يُستخدم national ID كمعرف URL أو query key، ولا يُسجل خاماً في logs أو mapping tables. أي تطابق legacy يعتمد على HMAC/encrypted evidence ضمن workflow تحقق، وليس على phone وحده.

## Relationship foundation

تضيف C1 جدول `niam_citizen_relationships` بعلاقة account أو legacy account إلى citizen/patient، مع source kind وrelationship type وscope وstatus وvalidity وrevocation وverification metadata. الإضافة additive ولا تنفذ backfill أو dual-write أو merge تلقائياً.

## حالات الهوية

تتدرج الهوية من pending إلى verified/active وفق أدلة مسموحة، وتظل البيانات محدودة حتى اكتمال التحقق. collision أو merge أو deceased/merged record يحتاج مساراً مستقلاً وتدقيقاً قبل أي تعديل.
