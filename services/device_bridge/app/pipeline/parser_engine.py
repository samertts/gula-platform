from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

STX = 0x02
ETX = 0x03
ENQ = 0x05
ACK = 0x06
NAK = 0x15
EOT = 0x04
CR = 0x0D
LF = 0x0A


@dataclass(slots=True)
class ParsedResult:
    test_code: str
    value: float
    unit: str
    # IA-050: what the instrument said about its own result, carried verbatim
    # and uninterpreted. Defaulted so the legacy single-line ParserEngine and
    # every existing caller keep working unchanged.
    reference_range: str = ""
    abnormal_flags: str = ""
    result_status: str = ""
    completed_at: str = ""


@dataclass(slots=True)
class ASTMRecord:
    type: Literal["header", "patient", "result", "terminator", "unknown"]
    raw: str
    patient_id: str | None = None
    patient_name: str | None = None
    test_code: str | None = None
    value: str | None = None
    unit: str | None = None
    # IA-050. The analyzer sends these in the same positional record the parser
    # already splits, and they were dropped on the floor. They are carried
    # verbatim as opaque strings: nothing here interprets an abnormal flag, parses
    # a reference range into bounds, maps an ASTM status code, or reads a vendor
    # date format. Not discarding what the instrument said is not the same as
    # deciding what it means.
    sequence: str | None = None
    reference_range: str | None = None
    abnormal_flags: str | None = None
    nature_of_abnormality: str | None = None
    result_status: str | None = None
    completed_at: str | None = None


class ParserError(ValueError):
    pass


class ASTMBuffer:
    """Byte-level ASTM frame assembler supporting fragmentation and checksum bytes."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def append(self, data: bytes) -> None:
        self._buffer.extend(data)

    def discard_pending(self) -> int:
        """Drop the retained bytes and return how many there were.

        The buffer stays dumb about policy: it reports what it holds and
        forgets on request, and the pipeline decides when a partial frame has
        grown past the point of being a partial frame -- and records the
        discard, because IA-039's invariant is that nothing is lost silently.
        """
        discarded = len(self._buffer)
        self._buffer.clear()
        return discarded

    @property
    def pending_bytes(self) -> int:
        """Bytes retained for continuation after the last extract_frames().

        Read-only. It is what distinguishes "the rest of this frame has not
        arrived yet" from "these bytes were discarded": extract_frames clears
        the buffer outright when it finds no STX, and zero frames plus zero
        pending bytes is the only way to observe that loss from outside.
        """
        return len(self._buffer)

    def extract_frames(self) -> list[tuple[bytes, str]]:
        """Return (frame_payload_without_stx_etx, checksum_hex) tuples."""
        frames: list[tuple[bytes, str]] = []

        while True:
            try:
                stx_index = self._buffer.index(STX)
            except ValueError:
                self._buffer.clear()
                break

            if stx_index > 0:
                del self._buffer[:stx_index]

            try:
                etx_index = self._buffer.index(ETX, 1)
            except ValueError:
                break

            checksum_start = etx_index + 1
            checksum_end = checksum_start + 2
            if len(self._buffer) < checksum_end:
                break

            payload = bytes(self._buffer[1:etx_index])
            checksum_hex = bytes(self._buffer[checksum_start:checksum_end]).decode("ascii", errors="ignore")

            # Optional CR/LF after checksum.
            consumed = checksum_end
            if len(self._buffer) > consumed and self._buffer[consumed] == CR:
                consumed += 1
            if len(self._buffer) > consumed and self._buffer[consumed] == LF:
                consumed += 1

            del self._buffer[:consumed]
            frames.append((payload, checksum_hex.upper()))

        return frames


def calculate_checksum(payload: bytes) -> str:
    checksum = sum(payload) % 256
    return format(checksum, "02X")


def validate_checksum(payload: bytes, received_checksum: str) -> None:
    expected = calculate_checksum(payload)
    if expected != received_checksum.upper():
        raise ParserError(f"Checksum mismatch: expected {expected}, received {received_checksum}")


class ASTMParser:
    def parse_frame(self, payload: bytes) -> list[ASTMRecord]:
        text = payload.decode("ascii", errors="replace")
        lines = [line for line in text.split("\r") if line]
        return [self.parse_line(line) for line in lines]

    def parse_line(self, line: str) -> ASTMRecord:
        parts = line.split("|")
        if not parts:
            return ASTMRecord(type="unknown", raw=line)

        marker = parts[0]
        record_type = marker[1] if len(marker) > 1 else marker[:1]

        if record_type == "H":
            return ASTMRecord(type="header", raw=line)
        if record_type == "P":
            patient_id = parts[3] if len(parts) > 3 else ""
            patient_name = parts[5] if len(parts) > 5 else ""
            return ASTMRecord(type="patient", raw=line, patient_id=patient_id, patient_name=patient_name)
        if record_type == "R":
            raw_test = parts[2] if len(parts) > 2 else ""
            test_code = raw_test.split("^")[-1] if raw_test else ""

            def field(index: int) -> str:
                return parts[index] if len(parts) > index else ""

            # ASTM E1394 result record, by position:
            #   2 test id | 3 value | 4 units | 5 reference range |
            #   6 abnormal flags | 7 nature of abnormality | 8 result status |
            #   11 started at | 12 completed at
            # The first three were already read this way; the rest were dropped.
            return ASTMRecord(
                type="result",
                raw=line,
                # The record's own sequence number, also dropped until now. It
                # is per-message and restarts, so it is NOT a message identity
                # and does not make exactly-once delivery possible on its own --
                # see test_the_parser_does_not_retain_a_message_identity.
                sequence=field(1),
                test_code=test_code,
                value=field(3),
                unit=field(4),
                reference_range=field(5),
                abnormal_flags=field(6),
                nature_of_abnormality=field(7),
                result_status=field(8),
                completed_at=field(12),
            )
        if record_type == "L":
            return ASTMRecord(type="terminator", raw=line)

        return ASTMRecord(type="unknown", raw=line)


class ASTMMessageBuilder:
    """Builds patient-bound result rows from parsed ASTM records."""

    def __init__(self) -> None:
        self.current_patient_id: str | None = None
        self.current_patient_name: str | None = None

    def process_records(self, records: list[ASTMRecord]) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for record in records:
            if record.type == "patient":
                self.current_patient_id = record.patient_id
                self.current_patient_name = record.patient_name
            elif record.type == "result":
                results.append(
                    {
                        "patient_id": self.current_patient_id or "UNKNOWN",
                        "test_code": record.test_code or "",
                        "value": record.value or "",
                        "unit": record.unit or "",
                        # IA-050: carried verbatim, uninterpreted.
                        "reference_range": record.reference_range or "",
                        "abnormal_flags": record.abnormal_flags or "",
                        "nature_of_abnormality": record.nature_of_abnormality or "",
                        "result_status": record.result_status or "",
                        "completed_at": record.completed_at or "",
                    }
                )
            elif record.type == "terminator":
                self.current_patient_id = None
                self.current_patient_name = None

        return results


class ParserEngine:
    """Backward-compatible single-line parser for simple ASTM-like samples."""

    def __init__(self) -> None:
        self._line_buffer = ""

    def parse(self, raw: str) -> ParsedResult:
        token = []
        fields: list[str] = []
        in_field = False

        for ch in raw.strip():
            if ch == "|":
                if in_field:
                    fields.append("".join(token).strip())
                    token = []
                in_field = True
                continue
            if in_field:
                token.append(ch)

        if token:
            fields.append("".join(token).strip())

        fields = [f for f in fields if f]
        if len(fields) < 3:
            raise ParserError(f"Expected at least 3 fields, got {len(fields)}: {raw!r}")

        try:
            value = float(fields[1])
        except ValueError as exc:
            raise ParserError(f"Invalid numeric value: {fields[1]!r}") from exc

        return ParsedResult(test_code=fields[0], value=value, unit=fields[2])

    def feed(self, chunk: str) -> list[ParsedResult]:
        """Incrementally parse newline-delimited records for legacy pipeline tests."""
        self._line_buffer += chunk
        lines = self._line_buffer.split("\n")
        self._line_buffer = lines.pop() if lines else ""

        parsed: list[ParsedResult] = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            parsed.append(self.parse(cleaned))
        return parsed
