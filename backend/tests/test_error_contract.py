from __future__ import annotations

from app.core.error_contract import (
    build_error_payload,
    public_http_detail,
    stable_http_detail,
    validation_details,
)


def test_build_error_payload_keeps_legacy_fields_and_adds_canonical_fields() -> None:
    payload = build_error_payload(
        status_code=409,
        message="Conflict",
        detail_ar="يوجد تعارض.",
        details={"field": "version"},
        request_id="req-123",
        timestamp="2026-08-12T00:00:00+00:00",
    )

    assert payload == {
        "code": "CONFLICT",
        "message": "Conflict",
        "details": {"field": "version"},
        "request_id": "req-123",
        "timestamp": "2026-08-12T00:00:00+00:00",
        "detail": "Conflict",
        "detail_ar": "يوجد تعارض.",
    }


def test_public_http_detail_does_not_echo_structured_or_server_error_details() -> None:
    assert public_http_detail({"secret": "do-not-echo"}, status_code=400) == (
        "Request failed.",
        {},
    )
    assert public_http_detail("database password", status_code=500) == (
        "An unexpected error occurred. Please try again later.",
        {},
    )


def test_validation_details_omits_submitted_input_values() -> None:
    details = validation_details(
        [
            {
                "loc": ("body", "patient_id"),
                "type": "value_error",
                "msg": "invalid patient id",
                "input": "secret-patient-value",
                "ctx": {"secret": "do-not-echo"},
            }
        ]
    )

    assert details == {
        "errors": [
            {
                "loc": ["body", "patient_id"],
                "type": "value_error",
                "message": "invalid patient id",
            }
        ]
    }
    assert "secret-patient-value" not in str(details)
    assert "do-not-echo" not in str(details)


def test_starlette_http_errors_use_canonical_payload() -> None:
    import json

    from app.factory import _http_exception_handler
    from starlette.exceptions import HTTPException
    from starlette.requests import Request

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/missing",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        }
    )
    response = _http_exception_handler(request, HTTPException(status_code=404, detail="missing"))
    body = json.loads(response.body)

    assert response.status_code == 404
    assert body["code"] == "NOT_FOUND"
    assert body["message"] == "missing"
    assert body["detail_ar"] == "المورد المطلوب غير موجود."
    assert {"request_id", "timestamp", "details"}.issubset(body)


def test_stable_http_detail_is_preserved_only_for_exact_shape() -> None:
    detail = {
        "code": "DOWNLOAD_BLOCKED_BY_DATA_SAVER",
        "message": "Data saver restrictions prevent this download.",
    }
    assert stable_http_detail(detail, status_code=409) == (
        "Data saver restrictions prevent this download.",
        {},
        "DOWNLOAD_BLOCKED_BY_DATA_SAVER",
    )
    assert stable_http_detail({"code": "OK", "message": "x", "extra": 1}, status_code=409) is None
    assert stable_http_detail({"code": "lowercase", "message": "x"}, status_code=409) is None
    assert stable_http_detail(detail, status_code=500) is None


def test_factory_handler_preserves_guls_stable_code_without_arabic_override() -> None:
    import json

    from app.factory import _http_exception_handler
    from starlette.exceptions import HTTPException
    from starlette.requests import Request

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/localization/language-packs/fa/download",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        }
    )
    response = _http_exception_handler(
        request,
        HTTPException(
            status_code=409,
            detail={
                "code": "DOWNLOAD_BLOCKED_BY_DATA_SAVER",
                "message": "Data saver restrictions prevent this download.",
            },
        ),
    )
    body = json.loads(response.body)
    assert body["code"] == "DOWNLOAD_BLOCKED_BY_DATA_SAVER"
    assert body["message"] == "Data saver restrictions prevent this download."
    assert body["detail_ar"] == body["message"]
