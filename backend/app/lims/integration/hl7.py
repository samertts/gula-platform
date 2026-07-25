"""HL7 v2.x Protocol Handler for lab instrument communication.

Implements parsing of HL7 ORU^R01 (observation result) messages
commonly used by laboratory instruments and middleware (Roche,
Abbott, Siemens).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("gula.lims.integration.hl7")

# HL7 segment types used in lab results
MSH = "MSH"  # Message Header
PID = "PID"  # Patient Identification
OBR = "OBR"  # Observation Request
OBX = "OBX"  # Observation/Result
SPM = "SPM"  # Specimen
ORC = "ORC"  # Common Order
NTE = "NTE"  # Notes/Comments


@dataclass
class HL7Segment:
    """Parsed HL7 segment."""

    segment_type: str
    fields: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class HL7Message:
    """Parsed HL7 message."""

    segments: list[HL7Segment] = field(default_factory=list)
    raw: str = ""


@dataclass
class HL7Result:
    """Canonical result parsed from HL7 ORU message."""

    specimen_id: str = ""
    patient_id: str = ""
    test_code: str = ""
    test_name: str = ""
    value: str = ""
    unit: str = ""
    ref_range: str = ""
    abnormal_flag: str = ""
    status: str = ""
    instrument_result_id: str = ""
    result_status: str = ""


def parse_hl7_message(raw_message: str) -> HL7Message:
    """Parse an HL7 v2.x message into structured segments."""
    # HL7 uses <CR> (0x0D) as segment delimiter
    segment_strings = re.split(r"\r|\n", raw_message)
    segments: list[HL7Segment] = []

    for seg_str in segment_strings:
        seg_str = seg_str.strip()
        if not seg_str:
            continue

        fields = seg_str.split("|")
        seg_type = fields[0] if fields else ""
        segments.append(HL7Segment(segment_type=seg_type, fields=fields, raw=seg_str))

    return HL7Message(segments=segments)


def parse_oru_message(raw_message: str) -> list[HL7Result]:
    """Parse an HL7 ORU^R01 message into canonical results."""
    message = parse_hl7_message(raw_message)
    results: list[HL7Result] = []
    current = HL7Result()

    for seg in message.segments:
        if seg.segment_type == PID and len(seg.fields) > 2:
            current.patient_id = seg.fields[2] if len(seg.fields) > 2 else ""
            if len(seg.fields) > 3:
                current.patient_id = seg.fields[3]  # PID-3 is patient identifier

        elif seg.segment_type == SPM and len(seg.fields) > 1:
            # SPM-2: Specimen ID
            spm_fields = (
                seg.fields[1].split("^")
                if "|" in seg.raw
                else [seg.fields[1]]
                if len(seg.fields) > 1
                else []
            )
            current.specimen_id = spm_fields[0] if spm_fields else ""

        elif seg.segment_type == OBR:
            if len(seg.fields) > 2:
                placer = seg.fields[2] if seg.fields[2] else ""
                filler = seg.fields[3] if len(seg.fields) > 3 and seg.fields[3] else ""
                current.instrument_result_id = filler or placer

        elif seg.segment_type == OBX:
            if len(seg.fields) > 2:
                current.test_code = seg.fields[3].split("^")[0] if seg.fields[3] else ""
                current.test_name = (
                    seg.fields[3].split("^")[1] if seg.fields[3] and "^" in seg.fields[3] else ""
                )
                current.value = seg.fields[5] if len(seg.fields) > 5 and seg.fields[5] else ""
                current.unit = seg.fields[6] if len(seg.fields) > 6 and seg.fields[6] else ""
                current.ref_range = seg.fields[7] if len(seg.fields) > 7 and seg.fields[7] else ""
                current.abnormal_flag = (
                    seg.fields[8] if len(seg.fields) > 8 and seg.fields[8] else ""
                )
                current.result_status = (
                    seg.fields[11] if len(seg.fields) > 11 and seg.fields[11] else ""
                )

                results.append(current)
                current = HL7Result(specimen_id=current.specimen_id, patient_id=current.patient_id)

    return results


def build_hl7_ack(message_control_id: str, ack_code: str = "AA") -> str:
    """Build HL7 ACK response."""
    from datetime import datetime

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    return (
        f"MSH|^~\\&|LIS|LAB|SENDING_APP|SENDING_FAC|{now}||ACK|{message_control_id}|P|2.5.1\r"
        f"MSA|{ack_code}|{message_control_id}\r"
    )
