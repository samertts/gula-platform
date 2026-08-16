from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import ENV
from app.security.dependencies import require_permission
from app.services.staging_tabular_import import MAX_FILE_BYTES, TabularImportError, load_nid_cases

router = APIRouter(
    prefix="/staging/import",
    tags=["staging-import"],
    dependencies=[Depends(require_permission("integration:manage"))],
)


@router.post("/nid-cases/validate")
async def validate_nid_cases_file(file: UploadFile = File(...)) -> dict[str, object]:
    """Validate synthetic NID cases from CSV/XLSX without persisting them."""
    if ENV.lower() not in {"development", "staging", "test"}:
        raise HTTPException(status_code=404, detail="Staging import is disabled")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise HTTPException(status_code=415, detail="Only CSV and XLSX files are accepted")

    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 5 MiB limit")

    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="gula-staging-", suffix=suffix, delete=False) as handle:
            handle.write(content)
            temporary_path = handle.name
        cases = load_nid_cases(temporary_path)
        return {
            "valid": True,
            "persisted": False,
            "format": suffix[1:],
            "count": len(cases),
            "cases": [
                {
                    "case_id": case.case_id,
                    "expected_status": case.expected_status,
                    "expected_http_status": case.expected_http_status,
                }
                for case in cases
            ],
        }
    except TabularImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()
        if temporary_path:
            with suppress(FileNotFoundError):
                os.unlink(temporary_path)
