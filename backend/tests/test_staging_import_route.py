from __future__ import annotations

from io import BytesIO

from app.routes.staging_import import validate_nid_cases_file
from fastapi import UploadFile


async def test_validate_nid_cases_upload_is_non_persistent():
    payload = (
        b"case_id,synthetic_nid,expected_status,expected_http_status\n"
        b"valid-1,100000000001,valid,200\n"
    )
    upload = UploadFile(filename="nid-cases.csv", file=BytesIO(payload))

    result = await validate_nid_cases_file(upload)

    assert result["valid"] is True
    assert result["persisted"] is False
    assert result["count"] == 1
    assert result["cases"] == [
        {"case_id": "valid-1", "expected_status": "valid", "expected_http_status": 200},
    ]
    assert "synthetic_nid" not in result["cases"][0]
