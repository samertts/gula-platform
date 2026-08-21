# إعداد تشغيل FastAPI وGunicorn/Uvicorn في GULA

## الهدف

يستخدم GULA Gunicorn لإدارة عمليات متعددة، مع worker ASGI مخصص مبني على Uvicorn. الإعدادات الافتراضية محافظة على الذاكرة وتضع سقفاً للتزامن داخل كل worker، مع إعادة تدوير العمال بعد عدد كبير من الطلبات لتقليل أثر التسربات التدريجية.

## الإعدادات الافتراضية

| المتغير | الافتراضي | الغرض |
|---|---:|---|
| `WEB_CONCURRENCY` | `2` | عدد عمليات Gunicorn؛ يُرفع بعد القياس فقط |
| `UVICORN_LIMIT_CONCURRENCY` | `400` | سقف التزامن لكل worker |
| `UVICORN_TIMEOUT_KEEP_ALIVE` | `5` | مهلة keep-alive بالثواني |
| `UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN` | `30` | زمن الإغلاق الهادئ |
| `UVICORN_LIMIT_MAX_REQUESTS` | `10000` | إعادة تدوير worker بعد عدد الطلبات |
| `GUNICORN_TIMEOUT` | `60` | مهلة worker الكلية |
| `GUNICORN_GRACEFUL_TIMEOUT` | `30` | مهلة الإنهاء الهادئ |
| `GUNICORN_KEEPALIVE` | `5` | keep-alive في Gunicorn |
| `GUNICORN_MAX_REQUESTS` | `10000` | تدوير worker |
| `GUNICORN_MAX_REQUESTS_JITTER` | `1000` | منع إعادة تشغيل العمال جميعاً في الوقت نفسه |
| `GUNICORN_BACKLOG` | `2048` | طابور الاتصالات المقبولة من نظام التشغيل |

تُمرر القيم من البيئة ولا توجد أسرار أو بيانات حساسة في ملف الإعداد. `preload_app` غير مستخدم عمداً؛ يجب عدم مشاركة اتصالات PostgreSQL أو Redis قبل fork.

## التشغيل

يستخدم Docker وRailway الملف `backend/start_railway.sh`. يمكن تشغيله محلياً بعد تجهيز قاعدة البيانات وRedis:

```bash
WEB_CONCURRENCY=2 \
UVICORN_LIMIT_CONCURRENCY=400 \
GUNICORN_MAX_REQUESTS=10000 \
GUNICORN_MAX_REQUESTS_JITTER=1000 \
./backend/start_railway.sh
```

لا تستخدم `ENV=test` لقياس الحمل، ولا تضبط `WEB_CONCURRENCY` على عدد كبير دون قياس RSS لكل worker وpool saturation في PostgreSQL وRedis.

## المعايرة

ابدأ بعاملين، ثم اختبر حمل I/O واقعي لمدة 5–15 دقيقة. سجّل p50 وp95 وp99، نسبة 429 و5xx، RSS، CPU، event-loop lag، زمن Redis، pool saturation، ووقت الاستجابة upstream. زد workers أو `UVICORN_LIMIT_CONCURRENCY` واحداً في كل مرة.

إذا ارتفع RSS مع التزامن، خفّض حد التزامن وحجم body والرفع والpagination. إذا ارتفع CPU مع RSS مستقر، افصل الأعمال CPU-heavy إلى queue أو خدمة worker. إذا ارتفع latency مع CPU منخفض، راجع PostgreSQL وRedis والـupstreams قبل زيادة العمال.

## الحماية الخارجية

هذه الإعدادات لا تستبدل CDN أو WAF أو Nginx. يجب تطبيق `client_max_body_size` و`limit_req` و`limit_conn` وupstream timeouts عند الحافة، ثم إبقاء `GlobalRateLimitMiddleware` كطبقة داخلية. يجب أن يكون Redis مشتركاً في Production حتى لا يحصل كل worker على عداد rate limit مستقل.

## التحقق

يجب تشغيل الاختبارات التالية قبل الدمج:

```bash
cd backend
.venv/bin/pytest -q tests/test_runtime_server_config.py tests/test_global_rate_limit_middleware.py
sh -n start_railway.sh
python -m compileall -q app shared railway_startup_probe.py gula_uvicorn_worker.py
```

ثم يجب تشغيل suite Backend الرسمية وTypeScript وproduction build. لا يُعتبر الإعداد جاهزاً للإنتاج قبل تشغيل اختبار staging متعدد workers مع PostgreSQL وRedis فعليين.

## مراجع

[1]: https://fastapi.tiangolo.com/deployment/server-workers/ "FastAPI — Server Workers"
[2]: https://uvicorn.dev/settings/ "Uvicorn — Settings"
[3]: https://gunicorn.org/reference/settings/ "Gunicorn — Settings Reference"
