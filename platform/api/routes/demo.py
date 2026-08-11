"""Isolated, synthetic-only demo access for the GULA platform API.

This module deliberately exposes no clinical resource and never delegates to patient,
order, sample, or result services. It is safe to mount beside the production API.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status

router = APIRouter()

_DEMO_TTL_SECONDS = 20 * 60
_DEMO_ATTEMPT_WINDOW_SECONDS = 60
_DEMO_ATTEMPT_LIMIT = 8
_ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
_SECRET_FROM_ENV = os.getenv("DEMO_SESSION_SECRET")
_DEMO_SECRET = _SECRET_FROM_ENV or "development-only-demo-secret-change-before-production"
_attempts: dict[str, tuple[int, float]] = {}
_revoked_sessions: dict[str, float] = {}

_DEMO_DASHBOARD: dict[str, Any] = {
    "environment": "demo",
    "user": {
        "name": "د. سارة",
        "role": "مشرفة المختبر — عرض توضيحي",
        "facility": "مختبر جولا التدريبي",
    },
    "summary": [
        {"label": "عينات مستلمة", "value": "128", "note": "+8.6% مقارنة بالأسبوع السابق", "trend": "up"},
        {"label": "قيد المعالجة", "value": "24", "note": "ضمن الزمن المستهدف", "trend": "neutral"},
        {"label": "بانتظار مراجعة", "value": "7", "note": "تتطلب اعتماداً تدريبياً", "trend": "down"},
        {"label": "تقارير مكتملة", "value": "96", "note": "+12.4% مقارنة بالأسبوع السابق", "trend": "up"},
    ],
    "workload": [
        {"day": "السبت", "value": 44},
        {"day": "الأحد", "value": 61},
        {"day": "الاثنين", "value": 58},
        {"day": "الثلاثاء", "value": 72},
        {"day": "الأربعاء", "value": 66},
        {"day": "الخميس", "value": 81},
        {"day": "الجمعة", "value": 53},
    ],
    "queue": [
        {"id": "TRN-1048", "type": "كيمياء سريرية", "status": "جاهز للمراجعة", "urgency": "priority", "updated": "منذ 8 دقائق"},
        {"id": "TRN-1047", "type": "تعداد دم كامل", "status": "قيد المعالجة", "urgency": "normal", "updated": "منذ 13 دقيقة"},
        {"id": "TRN-1046", "type": "مؤشرات حيوية", "status": "تم التحقق", "urgency": "normal", "updated": "منذ 21 دقيقة"},
        {"id": "TRN-1045", "type": "كيمياء سريرية", "status": "قيد المعالجة", "urgency": "normal", "updated": "منذ 33 دقيقة"},
    ],
    "activity": [
        {"id": "activity-1", "title": "تم التحقق من عينة تدريبية", "detail": "TRN-1046 — لا توجد بيانات حقيقية", "time": "منذ 6 دقائق", "state": "done"},
        {"id": "activity-2", "title": "أُحيلت نتيجة للمراجعة التدريبية", "detail": "TRN-1048 — اعتماد محاكٍ مطلوب", "time": "منذ 14 دقيقة", "state": "review"},
        {"id": "activity-3", "title": "أُنشئ طلب تدريبي جديد", "detail": "TRN-1049 — مسار الاستقبال", "time": "منذ 20 دقيقة", "state": "new"},
    ],
    "safety": {"verifiedSamples": 96, "pendingReview": 7, "auditEvents": 184},
}


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes | None:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, UnicodeEncodeError):
        return None


def _sign(payload: str) -> str:
    return _encode(hmac.new(_DEMO_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest())


def _new_token() -> str:
    now = int(time.time())
    claims = {
        "environment": "demo",
        "sessionId": secrets.token_urlsafe(18),
        "issuedAt": now,
        "expiresAt": now + _DEMO_TTL_SECONDS,
    }
    payload = _encode(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    return f"{payload}.{_sign(payload)}"


def _claims_from_request(request: Request) -> dict[str, Any] | None:
    token = request.cookies.get("gula_demo")
    if not token or "." not in token:
        return None
    payload, signature = token.rsplit(".", 1)
    expected = _sign(payload)
    if not hmac.compare_digest(signature, expected):
        return None
    decoded = _decode(payload)
    if not decoded:
        return None
    try:
        claims = json.loads(decoded)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if (
        claims.get("environment") != "demo"
        or not isinstance(claims.get("sessionId"), str)
        or not isinstance(claims.get("expiresAt"), int)
        or claims["expiresAt"] <= time.time()
    ):
        return None
    revoked_until = _revoked_sessions.get(claims["sessionId"])
    if revoked_until and revoked_until > time.time():
        return None
    if revoked_until:
        _revoked_sessions.pop(claims["sessionId"], None)
    return claims


def _request_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _can_start_demo(request: Request) -> bool:
    now = time.monotonic()
    request_ip = _request_ip(request)
    count, reset_at = _attempts.get(request_ip, (0, now + _DEMO_ATTEMPT_WINDOW_SECONDS))
    if now >= reset_at:
        count, reset_at = 0, now + _DEMO_ATTEMPT_WINDOW_SECONDS
    if count >= _DEMO_ATTEMPT_LIMIT:
        return False
    _attempts[request_ip] = (count + 1, reset_at)
    return True


def _require_production_secret() -> None:
    if _ENVIRONMENT == "production" and not _SECRET_FROM_ENV:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Demo access is temporarily unavailable.")


def _set_no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"


@router.get("/status")
async def demo_status(response: Response) -> dict[str, str]:
    """Public, non-sensitive status used solely by the access screen."""
    _set_no_store(response)
    return {
        "status": "healthy",
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "message": "الخدمات الأساسية تعمل بصورة طبيعية",
    }


@router.post("/session", status_code=status.HTTP_201_CREATED)
async def create_demo_session(request: Request, response: Response) -> dict[str, Any]:
    _require_production_secret()
    if not _can_start_demo(request):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many demo requests. Please wait before trying again.")
    _set_no_store(response)
    response.set_cookie(
        key="gula_demo",
        value=_new_token(),
        max_age=_DEMO_TTL_SECONDS,
        httponly=True,
        secure=_ENVIRONMENT == "production",
        samesite="strict",
        path="/",
    )
    return {"environment": "demo", "expiresInSeconds": _DEMO_TTL_SECONDS}


@router.get("/dashboard")
async def get_demo_dashboard(request: Request, response: Response) -> dict[str, Any]:
    if not _claims_from_request(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="A valid demo session is required.")
    _set_no_store(response)
    return {**_DEMO_DASHBOARD, "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def end_demo_session(request: Request, response: Response) -> Response:
    claims = _claims_from_request(request)
    if claims:
        _revoked_sessions[claims["sessionId"]] = claims["expiresAt"]
    _set_no_store(response)
    response.delete_cookie(key="gula_demo", path="/", httponly=True, secure=_ENVIRONMENT == "production", samesite="strict")
    return response
