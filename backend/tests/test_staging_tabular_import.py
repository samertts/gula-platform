from __future__ import annotations

import csv

import pytest
from app.services.staging_tabular_import import TabularImportError, load_nid_cases
from openpyxl import Workbook

HEADER = ["case_id", "synthetic_nid", "expected_status", "expected_http_status"]
ROWS = [
    ["valid-1", "100000000001", "valid", "200"],
    ["invalid-1", "100000000002", "invalid", "200"],
    ["rate-limit", "100000000005", "error", "429"],
]


def _write_csv(path):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(ROWS)


def _write_xlsx(path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(HEADER)
    for row in ROWS:
        sheet.append(row)
    workbook.save(path)


def test_load_synthetic_nid_cases_from_csv(tmp_path):
    path = tmp_path / "nid-cases.csv"
    _write_csv(path)
    cases = load_nid_cases(path)
    assert [case.case_id for case in cases] == ["valid-1", "invalid-1", "rate-limit"]
    assert cases[0].synthetic_nid == "100000000001"


def test_load_synthetic_nid_cases_from_xlsx(tmp_path):
    path = tmp_path / "nid-cases.xlsx"
    _write_xlsx(path)
    cases = load_nid_cases(path)
    assert len(cases) == 3
    assert cases[-1].expected_http_status == 429


def test_reject_duplicate_case_id(tmp_path):
    path = tmp_path / "duplicate.csv"
    _write_csv(path)
    path.write_text(path.read_text().replace("invalid-1", "valid-1"), encoding="utf-8")
    with pytest.raises(TabularImportError, match="duplicated"):
        load_nid_cases(path)


def test_reject_formula_like_cell(tmp_path):
    path = tmp_path / "formula.csv"
    path.write_text(
        "case_id,synthetic_nid,expected_status,expected_http_status\n"
        '=HYPERLINK("x"),100000000001,valid,200\n',
        encoding="utf-8",
    )
    with pytest.raises(TabularImportError, match="formula-like"):
        load_nid_cases(path)


def test_reject_wrong_columns(tmp_path):
    path = tmp_path / "wrong.csv"
    path.write_text("case_id,synthetic_nid\ncase,100000000001\n", encoding="utf-8")
    with pytest.raises(TabularImportError, match="invalid columns"):
        load_nid_cases(path)


def test_reject_csv_null_byte(tmp_path):
    path = tmp_path / "null.csv"
    path.write_bytes(b"case_id,synthetic_nid,expected_status,expected_http_status\x00\n")
    with pytest.raises(TabularImportError, match="null byte"):
        load_nid_cases(path)


def test_reject_xlsx_macro_archive(tmp_path):
    path = tmp_path / "macro.xlsx"
    _write_xlsx(path)
    import zipfile

    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("xl/vbaProject.bin", b"synthetic")
    with pytest.raises(TabularImportError, match="macros"):
        load_nid_cases(path)


def test_reject_xlsx_unsafe_archive_path(tmp_path):
    path = tmp_path / "unsafe.xlsx"
    _write_xlsx(path)
    import zipfile

    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("../escape.txt", b"synthetic")
    with pytest.raises(TabularImportError, match="unsafe path"):
        load_nid_cases(path)


def test_reject_oversized_cell(tmp_path):
    path = tmp_path / "large-cell.csv"
    path.write_text(
        "case_id,synthetic_nid,expected_status,expected_http_status\n"
        + ("x" * 4097)
        + ",100000000001,valid,200\n",
        encoding="utf-8",
    )
    with pytest.raises(TabularImportError, match="exceeds 4096"):
        load_nid_cases(path)
