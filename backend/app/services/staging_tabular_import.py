"""Safe tabular import for synthetic staging integration cases.

This module intentionally imports only a bounded NID test-case contract. It does
not create patients, citizens, identity records, or clinical data.
"""
from __future__ import annotations

import csv
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 20 * 1024 * 1024
MAX_CELL_CHARS = 4_096
MAX_COLUMNS = 32
MAX_ROWS = 1_000
ALLOWED_SUFFIXES = {".csv", ".xlsx"}
_REJECTED_XLSX_MEMBERS = {"vbaProject.bin"}
REQUIRED_COLUMNS = {"case_id", "synthetic_nid", "expected_status", "expected_http_status"}
ALLOWED_STATUS = {"valid", "invalid", "error"}
ALLOWED_HTTP = {200, 401, 403, 429, 500, 504}


class TabularImportError(ValueError):
    """Raised when a staging CSV/XLSX violates the bounded test contract."""


@dataclass(frozen=True)
class NIDCase:
    case_id: str
    synthetic_nid: str
    expected_status: str
    expected_http_status: int


def _reject_formula(value: Any, *, row: int, column: str) -> None:
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        raise TabularImportError(f"formula-like cell rejected at row={row}, column={column}")


def _clean_row(raw: dict[str, Any], *, row: int) -> dict[str, str]:
    normalized = {str(key).strip(): "" if value is None else str(value).strip() for key, value in raw.items()}
    if len(normalized) > MAX_COLUMNS:
        raise TabularImportError(f"input contains more than {MAX_COLUMNS} columns")
    for column, value in normalized.items():
        if len(value) > MAX_CELL_CHARS:
            raise TabularImportError(f"cell exceeds {MAX_CELL_CHARS} characters at row={row}, column={column}")
        _reject_formula(value, row=row, column=column)
    return normalized


def _validate_xlsx_archive(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            total_uncompressed = 0
            for member in archive.infolist():
                name = member.filename.replace("\\\\", "/")
                if name.startswith("/") or ".." in Path(name).parts:
                    raise TabularImportError("XLSX archive contains an unsafe path")
                if Path(name).name in _REJECTED_XLSX_MEMBERS or name.startswith("xl/externalLinks/"):
                    raise TabularImportError("XLSX macros and external links are not accepted")
                total_uncompressed += member.file_size
                if total_uncompressed > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                    raise TabularImportError("XLSX archive exceeds the uncompressed size limit")
    except zipfile.BadZipFile as exc:
        raise TabularImportError("invalid XLSX archive") from exc


def _parse_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise TabularImportError("input file does not exist")
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise TabularImportError("only .csv and .xlsx files are accepted")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise TabularImportError("input file exceeds the 5 MiB limit")

    if path.suffix.lower() == ".csv":
        with path.open("rb") as raw_handle:
            if b"\x00" in raw_handle.read():
                raise TabularImportError("CSV contains a null byte")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise TabularImportError("CSV header is required")
            if len(reader.fieldnames) > MAX_COLUMNS:
                raise TabularImportError(f"input contains more than {MAX_COLUMNS} columns")
            rows = [dict(row) for row in reader]
    else:
        _validate_xlsx_archive(path)
        workbook = load_workbook(path, read_only=True, data_only=False)
        try:
            sheet = workbook.active
            values = sheet.iter_rows(values_only=True)
            header_values = next(values, None)
            if not header_values:
                raise TabularImportError("XLSX header is required")
            headers = ["" if value is None else str(value).strip() for value in header_values]
            rows = [dict(zip(headers, row, strict=False)) for row in values]
        finally:
            workbook.close()

    if len(rows) > MAX_ROWS:
        raise TabularImportError(f"input contains more than {MAX_ROWS} rows")
    return rows


def load_nid_cases(path: str | Path) -> list[NIDCase]:
    """Load only synthetic NID cases; never writes to a database."""
    rows = _parse_rows(Path(path))
    if not rows:
        raise TabularImportError("at least one test case is required")

    first = _clean_row(rows[0], row=2)
    columns = set(first)
    if columns != REQUIRED_COLUMNS:
        missing = sorted(REQUIRED_COLUMNS - columns)
        extra = sorted(columns - REQUIRED_COLUMNS)
        raise TabularImportError(f"invalid columns; missing={missing}, extra={extra}")

    cases: list[NIDCase] = []
    seen: set[str] = set()
    for index, raw in enumerate(rows, start=2):
        row = _clean_row(raw, row=index)
        case_id = row["case_id"]
        synthetic_nid = row["synthetic_nid"]
        status = row["expected_status"].lower()
        try:
            http_status = int(row["expected_http_status"])
        except ValueError as exc:
            raise TabularImportError(f"expected_http_status must be numeric at row={index}") from exc
        if not case_id or case_id in seen:
            raise TabularImportError(f"case_id is empty or duplicated at row={index}")
        if not synthetic_nid.isdigit() or len(synthetic_nid) not in {12, 16}:
            raise TabularImportError(f"synthetic_nid must contain 12 or 16 digits at row={index}")
        if status not in ALLOWED_STATUS:
            raise TabularImportError(f"unsupported expected_status at row={index}")
        if http_status not in ALLOWED_HTTP:
            raise TabularImportError(f"unsupported expected_http_status at row={index}")
        seen.add(case_id)
        cases.append(NIDCase(case_id, synthetic_nid, status, http_status))
    return cases
