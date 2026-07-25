from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("gula.integration.standards.hl7")

HL7_SEGMENT_SEP = "\r"
HL7_FIELD_SEP = "|"
HL7_COMPONENT_SEP = "^"
HL7_REPETITION_SEP = "~"
HL7_ESCAPE_CHAR = "\\"
HL7_SUBCOMPONENT_SEP = "&"


@dataclass
class HL7Segment:
    name: str = ""
    fields: list[str] = field(default_factory=list)


@dataclass
class HL7Message:
    segments: list[HL7Segment] = field(default_factory=list)
    encoding_chars: str = (
        f"{HL7_COMPONENT_SEP}{HL7_REPETITION_SEP}{HL7_ESCAPE_CHAR}{HL7_SUBCOMPONENT_SEP}"
    )

    def to_str(self) -> str:
        lines: list[str] = []
        for seg in self.segments:
            lines.append(f"{seg.name}{HL7_FIELD_SEP}{HL7_FIELD_SEP.join(seg.fields)}")
        return HL7_SEGMENT_SEP.join(lines)

    @classmethod
    def parse(cls, raw: str) -> HL7Message:
        msg = cls()
        for line in raw.split(HL7_SEGMENT_SEP):
            line = line.strip()
            if not line:
                continue
            parts = line.split(HL7_FIELD_SEP, 1)
            seg = HL7Segment(name=parts[0])
            if len(parts) > 1:
                seg.fields = parts[1].split(HL7_FIELD_SEP)
            msg.segments.append(seg)
        return msg


class HL7Service:
    def __init__(self, version: str = "2.5.1"):
        self._version = version

    def create_message(self, segment_defs: list[tuple[str, list[str]]]) -> HL7Message:
        msg = HL7Message()
        for name, fields in segment_defs:
            msg.segments.append(HL7Segment(name=name, fields=fields))
        return msg

    def parse(self, raw: str) -> HL7Message:
        return HL7Message.parse(raw)

    def serialize(self, msg: HL7Message) -> str:
        return msg.to_str()

    def validate(self, raw: str) -> list[str]:
        errors: list[str] = []
        msg = HL7Message.parse(raw)
        if not msg.segments:
            errors.append("Empty HL7 message")
            return errors
        if msg.segments[0].name != "MSH":
            errors.append("First segment must be MSH")
        return errors

    def ack(self, raw: str, ack_code: str = "AA") -> str:
        msg = HL7Message.parse(raw)
        msh = msg.segments[0]
        if len(msh.fields) >= 9:
            sending_app = msh.fields[1] if len(msh.fields) > 1 else ""
            sending_facility = msh.fields[2] if len(msh.fields) > 2 else ""
            msg_id = msh.fields[8] if len(msh.fields) > 8 else ""
        else:
            sending_app = ""
            sending_facility = ""
            msg_id = ""
        [
            ["ACK", msh.fields[0] if msh.fields else ""],
            ["MSA", ack_code, msg_id],
            ["SFT", sending_app, sending_facility],
        ]
        ack_msg = self.create_message(
            [
                (
                    "MSH",
                    [sending_app, sending_facility, "", "", "", "", "", "", str(len(msg.segments))],
                ),
                ("MSA", [ack_code, msg_id]),
            ]
        )
        return ack_msg.to_str()

    def version(self) -> str:
        return self._version
