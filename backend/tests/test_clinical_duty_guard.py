from starlette.requests import Request
from fastapi import HTTPException
from types import SimpleNamespace
import pytest

from app.security.clinical_duty_guard import require_clinical_duty


def request_with_headers(headers=()):
    return Request({"type": "http", "method": "POST", "path": "/clinical/orders", "headers": [(k.lower().encode(), v.encode()) for k, v in headers]})


def test_login_without_duty_context_is_denied():
    with pytest.raises(HTTPException) as error:
        require_clinical_duty(request_with_headers(), SimpleNamespace(id=7), object(), "100")
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "DUTY_CONTEXT_REQUIRED"


def test_non_numeric_patient_scope_is_denied():
    request = request_with_headers((("X-Duty-Context-ID", "dctx-1"),))
    with pytest.raises(HTTPException) as error:
        require_clinical_duty(request, SimpleNamespace(id=7), object(), "temporary-health-id")
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "PATIENT_SCOPE_UNVERIFIED"
