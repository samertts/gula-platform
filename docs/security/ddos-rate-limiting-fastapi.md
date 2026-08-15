# DDoS وRate Limiting في FastAPI — GULA

## المبدأ

Rate limiting داخل FastAPI يحمي موارد التطبيق من الإساءة، لكنه ليس بديلاً عن مزود DDoS أو WAF أو load balancer. هجمات volumetric وL3/L4 يجب امتصاصها قبل الوصول إلى Uvicorn؛ أما FastAPI فيعالج إساءة استخدام L7، استهلاك الموارد غير المقيد، المسارات المكلفة، وتكرار محاولات المصادقة. تصنف OWASP API4:2023 الاستهلاك غير المقيد كمصدر محتمل لـDoS وزيادة التكلفة [1].

## ما تم تطبيقه في هذه الدفعة

أضيف `GlobalRateLimitMiddleware` بميزانية coarse قدرها `RATE_LIMIT_GLOBAL=300` طلباً لكل IP في نافذة `RATE_LIMIT_GLOBAL_WINDOW_SECONDS=60`. يستخدم Redis المشترك عبر limiter الحالي عندما يكون متاحاً، ويعيد `429` مع `Retry-After` وحقول `X-RateLimit-*`. استُثنيت health probes حتى لا يمنع limiter orchestrator من معرفة حالة الخدمة، بينما بقيت الحدود الخاصة بالمصادقة وAI والعمليات المؤسسية أكثر صرامة.

هذه الطبقة لا تلغي الحدود الموجودة في `backend/app/security/rate_limit.py`، بل تضيف budget عاماً قبلها. في Production يجب أن يكون Redis متاحاً ومشتركاً بين workers؛ in-memory fallback لا يقدم حماية موزعة ويجب مراقبته كحالة degraded.

## طبقات الحماية الموصى بها

| الطبقة | الضبط الموصى به |
|---|---|
| CDN/WAF | امتصاص volumetric DDoS، bot/challenge rules، geo/IP reputation، request size limits |
| Load balancer/Nginx | connection limits، request rate، body/header limits، TLS، timeouts، buffering |
| FastAPI | Redis-backed IP/user/identifier limits، 429، Retry-After، concurrency guard |
| Route policy | حدود منفصلة للمصادقة، reset، verification، AI، search، uploads، billing، pharmacy |
| Resource policy | body/upload limits، pagination caps، query timeouts، outbound client timeouts |
| Observability | 429 ratio، Redis health، latency، queue depth، active connections، CPU/memory |
| Recovery | circuit breaker، degraded mode واضح، rollback، runbook، provider escalation |

## أحدث الممارسات العملية

يجب تطبيق **multi-dimensional limits**: IP للطلبات العامة، user/tenant للمستخدم المصادق، HMAC identifier لمحاولات login/reset، وbudget مستقل للمسارات المكلفة. لا تعتمد على IP وحده خلف proxy، ولا تثق في `X-Forwarded-For` إلا من عناوين proxy موثوقة. توضح FastAPI أن proxy headers لا ينبغي قبولها من كل العناوين، بل عبر قائمة `forwarded-allow-ips` محددة [2].

استخدم Redis atomic operations أو Lua/token-bucket في البيئات متعددة workers، واجعل failure mode مقصوداً: في auth وhealth-data يفضّل fail-closed أو تقليل الميزانية عند فقد Redis؛ أما health endpoints فلا تُحجب عشوائياً. لا تُسجل email أو phone أو token في مفاتيح Redis أو logs؛ استخدم HMAC digest كما يفعل limiter الحالي.

أعد `429 Too Many Requests` مع `Retry-After` و`X-RateLimit-Limit` و`X-RateLimit-Remaining` و`X-RateLimit-Reset`. اجعل clients تحترم backoff مع jitter، ولا تجعل retries المتزامنة تضاعف الحمل. طبّق idempotency keys على العمليات المالية والصرفية الحساسة، لأن إعادة المحاولة الآلية ليست بديلاً عن idempotency.

ضع timeouts لكل outbound HTTP/DICOM/LIS/insurance/AI call، وحدد حجم response والتحميل والـpagination. لا تستخدم timeout واحداً ضخماً لكل المسارات. المسارات التي تنفذ AI أو تقارير ثقيلة يجب أن تستخدم queue/circuit breaker أو budget لكل tenant بدلاً من تنفيذ غير محدود داخل request.

## إعدادات مقترحة في البيئة

```dotenv
RATE_LIMIT_GLOBAL=300
RATE_LIMIT_GLOBAL_WINDOW_SECONDS=60
RATE_LIMIT_AUTH=10
RATE_LIMIT_PUBLIC=30
RATE_LIMIT_BLOCK_DURATION_SECONDS=3600
REDIS_URL=rediss://...
```

القيم السابقة نقطة بداية وليست SLA. يجب معايرتها من traffic baseline وp95/p99، مع استثناءات موثقة للـhealth probes وdevice gateways الموثوقة. لا تُفعّل `ALLOW_DEGRADED_REDIS=true` في Production إلا بقرار تشغيلي موثق وفترة قصيرة، لأنه يجعل budget غير مشترك بين workers.

## Nginx/WAF أمام FastAPI

يجب أن يطبق edge limits قبل وصول الطلب إلى Uvicorn. مثال مفاهيمي، يحتاج معايرة في بيئة GULA ولا ينبغي نسخه إلى Production دون load test:

```nginx
limit_req_zone $binary_remote_addr zone=gula_public:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=gula_conn:10m;

server {
    client_max_body_size 10m;
    client_header_timeout 10s;
    client_body_timeout 15s;
    keepalive_timeout 15s;
    send_timeout 15s;

    location /api/ {
        limit_req zone=gula_public burst=30 nodelay;
        limit_conn gula_conn 40;
        proxy_connect_timeout 3s;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;
        proxy_pass http://gula_backend;
    }
}
```

يجب ألا تكون limits في Nginx وFastAPI متناقضة بحيث تحجب traffic الشرعي أو تجعل health checks تفشل. لا تعتمد على Nginx وحده لتحديد user/tenant؛ هذه معلومات لا يملكها إلا التطبيق بعد المصادقة.

## الاختبارات ومعايير القبول

يجب أن تثبت الاختبارات أن global limiter يعيد 429 بعد تجاوز budget، وأن health probes لا تُستهلك، وأن CORS/auth/AI limits ما زالت تعمل، وأن Redis keys لا تحتوي بيانات خام، وأن proxy IP extraction لا يقبل spoofed headers من اتصال خارجي مباشر. يجب تنفيذ load test تدريجي في staging فقط، مع بيانات synthetic، وقياس p50/p95/p99 و429 و5xx وCPU وmemory وRedis latency.

لا يعتبر النظام محمياً من DDoS لمجرد نجاح unit tests. القبول النهائي يحتاج WAF/CDN evidence، اختبار burst، chaos لفقد Redis، اختبار worker متعدد، ومراجعة rollback. لا تُجرى اختبارات flood على Production أو على طرف ثالث دون موافقة مكتوبة.

## مراجع

[1]: https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/ "OWASP API4:2023 Unrestricted Resource Consumption"
[2]: https://fastapi.tiangolo.com/advanced/behind-a-proxy/ "FastAPI Behind a Proxy"
[3]: https://fastapi.tiangolo.com/advanced/middleware/ "FastAPI Advanced Middleware"
[4]: https://redis.io/docs/latest/develop/data-types/strings/ "Redis data types and atomic operations"
[5]: https://owasp.org/www-project-api-security/ "OWASP API Security Project"
