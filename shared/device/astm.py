from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger("gula.device.astm")


@dataclass
class ASTMResult:
    sequence: str = ""
    test_id: str = ""
    test_name: str = ""
    value: str = ""
    unit: str = ""
    abnormal_flags: str = ""
    reference_range: str = ""


class ASTMProtocol:
    STX = b"\x02"
    ETX = b"\x03"
    EOT = b"\x04"
    ENQ = b"\x05"
    ACK = b"\x06"
    NAK = b"\x15"
    CR = b"\r"

    FRAME_PATTERN = re.compile(rb"\x02(.*?)\x03(\w?)")

    @classmethod
    def parse_frame(cls, data: bytes) -> list[list[str]]:
        frames = []
        for match in cls.FRAME_PATTERN.finditer(data):
            content = match.group(1).decode("ascii", errors="replace")
            lines = content.split(cls.CR.decode())
            records = [line for line in lines if line.strip()]
            if records:
                frames.append(records)
        return frames

    @classmethod
    def parse_result_record(cls, record: str) -> ASTMResult | None:
        fields = record.split("|")
        if len(fields) < 3:
            return None
        result = ASTMResult()
        if len(fields) > 1:
            result.sequence = fields[1]
        if len(fields) > 2:
            result.test_id = fields[2]
        if len(fields) > 3:
            result.test_name = fields[3]
        if len(fields) > 4:
            result.value = fields[4]
        if len(fields) > 5:
            result.unit = fields[5]
        if len(fields) > 6:
            result.abnormal_flags = fields[6]
        if len(fields) > 7:
            result.reference_range = fields[7]
        return result
