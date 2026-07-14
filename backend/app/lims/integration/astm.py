"""ASTM E1394 / E1381 Protocol Handler for lab instrument communication.

Implements the ASTM serial protocol used by many hematology and chemistry
analyzers (Sysmex, Mindray, etc.).  Parses instrument frames and builds
canonical LIMS result objects.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.lims.integration.astm")


# ASTM frame types
FRAME_HEADER = "H"
FRAME_PATIENT = "P"
FRAME_ORDER = "O"
FRAME_RESULT = "R"
FRAME_COMMENT = "C"
FRAME_TERMINATOR = "L"
FRAME_QUERY = "Q"
FRAME_MANUFACTURER = "M"


@dataclass
class ASTMRecord:
    """Parsed ASTM record."""
    record_type: str
    fields: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class ASTMResult:
    """Canonical result parsed from ASTM message."""
    specimen_id: str = ""
    test_code: str = ""
    test_name: str = ""
    value: str = ""
    unit: str = ""
    ref_range: str = ""
    flag: str = ""
    instrument_result_id: str = ""
    raw_records: list[ASTMRecord] = field(default_factory=list)


def parse_astm_message(raw_message: str) -> list[ASTMResult]:
    """Parse a complete ASTM message into canonical results.

    Handles ASTM E1394 (frames separated by <CR><LF> or <CR>).
    Returns a list of ASTMResult objects.
    """
    lines = re.split(r"\r?\n|\r", raw_message)
    records: list[ASTMRecord] = []
    results: list[ASTMResult] = []
    current_result: ASTMResult = ASTMResult()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        record_type = line[0] if line else ""
        fields = line.split("|") if "|" in line else [line]

        record = ASTMRecord(record_type=record_type, fields=fields, raw=line)
        records.append(record)

        if record_type == FRAME_PATIENT and len(fields) > 1:
            current_result.specimen_id = fields[1] if len(fields) > 1 else ""

        elif record_type == FRAME_ORDER and len(fields) > 2:
            if len(fields) > 2 and fields[2]:
                current_result.test_code = fields[2]

        elif record_type == FRAME_RESULT and len(fields) > 2:
            current_result.test_code = fields[2] if len(fields) > 2 else current_result.test_code
            current_result.test_name = fields[3] if len(fields) > 3 else ""
            current_result.value = fields[4] if len(fields) > 4 else ""
            current_result.unit = fields[5] if len(fields) > 5 else ""
            current_result.ref_range = fields[6] if len(fields) > 6 else ""
            current_result.flag = fields[7] if len(fields) > 7 else ""
            current_result.instrument_result_id = fields[1] if len(fields) > 1 else ""
            current_result.raw_records = list(records)
            results.append(current_result)
            current_result = ASTMResult()

        elif record_type == FRAME_TERMINATOR:
            break

    return results


def build_astm_query(specimen_barcode: str, test_codes: list[str] | None = None) -> str:
    """Build an ASTM query message for a specimen."""
    seq = 1
    lines = [
        f"H|\\^&|||LIS|||||ASTM_E1394|{seq:04d}|",
        f"Q|1|{specimen_barcode}||ALL",
        f"L|1|N",
    ]
    return "\r".join(lines)


def serialize_astm_result(result: ASTMResult) -> str:
    """Serialize a result back to ASTM format (for device bridge responses)."""
    lines = [
        f"H|\\^&|||LIS|||||ASTM_E1394|0001|",
        f"P|1|{result.specimen_id}",
        f"O|1|{result.specimen_id}|{result.test_code}",
    ]
    if result.value:
        lines.append(
            f"R|1|{result.instrument_result_id}|{result.test_code}|"
            f"{result.test_name}|{result.value}|{result.unit}|"
            f"{result.ref_range}|{result.flag}"
        )
    lines.append("L|1|N")
    return "\r".join(lines)
