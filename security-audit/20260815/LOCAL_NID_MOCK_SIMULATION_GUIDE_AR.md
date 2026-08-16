# محاكاة موفر NID محلياً قبل الربط الخارجي

## الهدف والحدود

المحاكاة المحلية يجب أن تختبر **عقد الاتصال والسلوك الأمني** فقط، ولا تثبت أن موفر NID الرسمي يعمل فعلياً. استخدم أرقاماً اصطناعية مخصصة للاختبار، ولا تستخدم أرقاماً وطنية أو بيانات مواطنين حقيقية. لا يجوز أن تؤدي نتيجة mock إلى إنشاء هوية verified أو إلى قرار سريري.

في GULA توجد ثلاثة أوضاع للـNID: `stub` للمحاكاة الداخلية بلا شبكة، و`shadow` لاتصال خارجي مع إعادة نتيجة stub إلى التطبيق، و`live` لإعادة النتيجة بعد التحقق. المحاكاة المحلية تُستخدم لاختبار behavior يشبه `live`، لكنها لا تستبدل sandbox الرسمي [1].

## 1. حالات الاختبار الاصطناعية

استخدم عقداً ثابتاً يمكن التحقق منه آلياً:

| المعرّف الاصطناعي | النتيجة | الاستخدام |
|---|---|---|
| `100000000001` | `valid=true` | نجاح أساسي |
| `100000000002` | `valid=false` | هوية غير صالحة |
| `100000000003` | HTTP 401 | credential مرفوض |
| `100000000004` | HTTP 403 | scope غير كافٍ |
| `100000000005` | HTTP 429 | rate limit |
| `100000000006` | HTTP 500 | provider failure |
| `100000000007` | timeout | circuit breaker/retry |
| `100000000008` | JSON ناقص | schema validation |
| `100000000009` | JSON زائد أو malformed | رفض response |

هذه القيم اصطناعية ولا ينبغي تسجيلها في production أو إرسالها إلى جهة حكومية حقيقية.

## 2. Mock server بسيط محلياً

يمكن إنشاء mock server باستخدام FastAPI. احفظ الكود في ملف، ولا تشغّل كوداً من نص منسوخ مباشرة في shell:

```python
# /tmp/nid_mock_server.py
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import asyncio

app = FastAPI(title="NID Sandbox Mock")

class VerifyRequest(BaseModel):
    id: str

@app.post("/api/id/verify")
async def verify(request: VerifyRequest, x_api_key: str | None = Header(None)):
    if x_api_key != "local-nid-key":
        raise HTTPException(status_code=401, detail="invalid sandbox key")

    if request.id == "100000000003":
        raise HTTPException(status_code=401, detail="credential rejected")
    if request.id == "100000000004":
        raise HTTPException(status_code=403, detail="scope rejected")
    if request.id == "100000000005":
        raise HTTPException(status_code=429, detail="rate limited")
    if request.id == "100000000006":
        raise HTTPException(status_code=500, detail="provider failure")
    if request.id == "100000000007":
        await asyncio.sleep(20)
    if request.id == "100000000008":
        return {"source": "local_nid_mock"}
    if request.id == "100000000009":
        return {"valid": "yes", "source": "local_nid_mock"}
    if request.id == "100000000002":
        return {"valid": False, "source": "local_nid_mock"}
    return {"valid": True, "source": "local_nid_mock"}
```

شغّله في جلسة محلية منفصلة:

```bash
cd /home/ubuntu/gula-platform
uvicorn nid_mock_server:app --host 127.0.0.1 --port 18080
```

لا تستخدم هذا العنوان في staging الحقيقي؛ هو محلي فقط. ولأن preflight الخاص بـGULA يفرض HTTPS في staging، فإن HTTP المحلي يجب أن يقتصر على unit/contract tests أو يُوضع خلف reverse proxy محلي بشهادة test مخصصة. لا تجعل `verify=false` أو `CERT_NONE` قاعدة تشغيلية.

## 3. اختبار عقد HTTP مباشرة

اختبر request/response دون استدعاء التطبيق أولاً:

```bash
curl --fail-with-body --silent --show-error \
  -X POST http://127.0.0.1:18080/api/id/verify \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: local-nid-key' \
  -d '{"id":"100000000001"}'
```

يجب أن تكون النتيجة:

```json
{"valid":true,"source":"local_nid_mock"}
```

ثم اختبر الحالات السلبية، ولاحظ أن 401 و403 و429 و500 يجب ألا تتحول إلى `valid=true` أو success وهمي.

## 4. اختبار GULA في STUB

ابدأ دون أي mock network:

```bash
export GULA_ADAPTER_MODE_NID=stub
unset MOI_NID_API_URL MOI_NID_API_KEY
cd /home/ubuntu/gula-platform/backend
export PYTHONPATH=/home/ubuntu/gula-platform/backend:/home/ubuntu/gula-platform
pytest -q tests/test_gateway_modes.py tests/test_national_identity_production_guard.py
```

هذه المرحلة تثبت أن validation المحلي يعمل، وأن أرقام الطول غير الصحيحة ترفض، وأن المسارات الحساسة لا تعتبر stub تحققاً حكومياً.

## 5. اختبار استدعاء LIVE محلياً دون تعديل التطبيق

لأن كود GULA يتطلب HTTPS في بوابة staging، الأفضل اختبار `_live_response` عبر `httpx.MockTransport` أو monkeypatch بدلاً من تعطيل TLS. مثال unit test:

```python
from app.gateways.national_identity_gateway import NationalIdentityGateway
from app.gateways.mode import AdapterMode


def test_nid_live_contract_uses_mock_transport(monkeypatch):
    gateway = NationalIdentityGateway()
    gateway.mode = AdapterMode.LIVE
    monkeypatch.setenv("MOI_NID_API_URL", "https://nid.local.test")
    monkeypatch.setenv("MOI_NID_API_KEY", "local-nid-key")

    captured = {}

    def fake_http(method, url, **kwargs):
        captured.update(method=method, url=url, kwargs=kwargs)
        return {"valid": True, "source": "local_nid_mock"}

    monkeypatch.setattr(gateway, "_http", fake_http)
    result = gateway._live_response("100000000001")

    assert result["valid"] is True
    assert captured["method"] == "post"
    assert captured["url"] == "https://nid.local.test/api/id/verify"
    assert captured["kwargs"]["json"] == {"id": "100000000001"}
    assert captured["kwargs"]["headers"]["X-API-Key"] == "local-nid-key"
```

هذا الاختبار لا يرسل request خارجياً، لكنه يثبت endpoint path وheader وpayload. يجب عدم وضع `local-nid-key` في production أو في Git history.

## 6. اختبار SHADOW

اختبار SHADOW يجب أن يثبت أمرين معاً: أن استدعاء provider mock حدث، وأن caller لم يحصل على نتيجة mock مباشرة. في GULA الحالي، يعيد SHADOW نتيجة stub ويكتب نتيجة الاتصال في logging للمقارنة. يجب تقليل logging إلى metadata أو hash وعدم تسجيل رقم NID أو API key أو payload حساس.

```python
def test_shadow_calls_mock_but_returns_stub(monkeypatch):
    gateway = NationalIdentityGateway()
    gateway.mode = AdapterMode.SHADOW
    calls = []

    def fake_live(national_id: str):
        calls.append(national_id)
        return {"valid": True, "source": "local_nid_mock"}

    monkeypatch.setattr(gateway, "_live_response", fake_live)
    result = gateway._do_call("verify_national_id", national_id="100000000001")

    assert calls == ["100000000001"]
    assert result["source"].startswith("stub_")
```

## 7. تشغيل preflight الخاص بـGULA

لا تستخدم `STAGING_REQUIRE_EXTERNAL_NID=true` إلا عندما يكون الاختبار موجهاً إلى sandbox أو mock HTTPS معتمد للـstaging. يرفض preflight الوضع `stub` في external gate، ويفرض Redis TLS وCORS HTTPS وallowlist:

```bash
cd /home/ubuntu/gula-platform
ENV=staging \
ALLOW_DEGRADED_REDIS=false \
REDIS_URL=rediss://redis-staging.internal:6380/0 \
CORS_ALLOWED_ORIGINS=https://staging.gula-platform.example \
GULA_ADAPTER_MODE_NID=shadow \
MOI_NID_API_URL=https://nid.local.test \
MOI_NID_API_KEY=local-nid-key \
GOV_CONNECTOR_URLS=https://connector.local.test \
STAGING_EGRESS_ALLOWLIST=nid.local.test:443,connector.local.test:443 \
STAGING_REQUIRE_EXTERNAL_NID=true \
python3 scripts/staging_preflight.py
```

في تشغيل محلي HTTP، اترك `STAGING_REQUIRE_EXTERNAL_NID=false` واستخدم unit/contract mock tests فقط. لا تتجاوز شرط HTTPS بتغيير preflight في الفرع المشترك.

## 8. اختبارات الفشل المطلوبة

يجب أن يمر mock contract بالاختبارات التالية:

| الحالة | المتوقع |
|---|---|
| API key ناقص | 401، لا fallback إلى verified |
| 403 | رفض authorization وتسجيل metadata فقط |
| 429 | retry محدود مع backoff، ثم degraded result |
| timeout | timeout hard deadline وcircuit breaker |
| 5xx | retry محدود، ثم failure واضح |
| JSON ناقص | schema validation failure |
| `valid` من نوع string | رفض type mismatch |
| response كبير جداً | رفض أو حد حجم واضح |
| تكرار الطلب | idempotency/correlation behavior موثق |
| raw NID في logs | فشل اختبار privacy |
| mock غير متاح | لا success وهمي |

شغّل الاختبارات المحلية الحالية مع الاختبار الجديد:

```bash
cd /home/ubuntu/gula-platform/backend
export PYTHONPATH=/home/ubuntu/gula-platform/backend:/home/ubuntu/gula-platform
pytest -q tests/test_gateway_modes.py tests/test_staging_preflight.py tests/test_national_identity_production_guard.py
```

## 9. الانتقال من mock إلى sandbox الرسمي

بعد نجاح mock، لا تنتقل مباشرة إلى `live`. استخدم الترتيب التالي: أولاً sandbox رسمي منفصل، ثم شهادة TLS أو mTLS، ثم sandbox API key، ثم `GULA_ADAPTER_MODE_NID=shadow`، ثم مقارنة منظمة لمدة زمنية محددة، ثم اختبار cohort اصطناعي، ثم تقرير schema/latency/error-rate، ثم موافقة الأمن ومالك التكامل، وأخيراً `live` محدود في staging فقط.

لا يخرج النظام من `SAFE_STOP` عند نجاح mock. الخروج يتطلب دليلاً من sandbox الرسمي، وتحققاً من العزل وRedis/PostgreSQL متعدد العمال وbrowser CSRF/CORS وegress وrollback [2].

## مراجع

[1]: `../../backend/app/gateways/national_identity_gateway.py` — أوضاع NID والعقد والـendpoint.

[2]: `STAGING_NID_GOVERNMENT_CONNECTORS_RUNBOOK_AR.md` — runbook Staging ومعايير SAFE_STOP.

[3]: `../../scripts/staging_preflight.py` — فحص الإعدادات fail-closed.
