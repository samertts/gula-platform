from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app._compat import UTC
from app.pipeline.parser_engine import ParsedResult

TEST_NAME_MAP = {
    "HEMOGLOBIN": "Hemoglobin",
    "HB": "Hemoglobin",
    "HGB": "Hemoglobin",
}


@dataclass(slots=True)
class NormalizedResult:
    patient_id: str
    device_id: str
    test_code: str
    test_name: str
    value: float
    unit: str
    reference_range: str
    timestamp: datetime
    status: str
    # IA-050. What the instrument itself reported, carried verbatim and
    # uninterpreted. Nothing here decides what an abnormal flag means, parses a
    # reference range into bounds, maps an ASTM status code, or reads a vendor
    # date format -- those are clinical and terminology decisions. This only
    # stops the bridge discarding them.
    device_abnormal_flags: str = ""
    device_nature_of_abnormality: str = ""
    device_result_status: str = ""
    device_completed_at: str = ""


class Normalizer:
    def transform(
        self,
        data: ParsedResult,
        *,
        patient_id: str,
        device_id: str,
        reference_range: str = "",
        nature_of_abnormality: str = "",
    ) -> NormalizedResult:
        return NormalizedResult(
            patient_id=patient_id,
            device_id=device_id,
            test_code=data.test_code,
            test_name=TEST_NAME_MAP.get(data.test_code.upper(), data.test_code),
            value=data.value,
            unit=data.unit,
            # The instrument's own reference range when it sent one; the caller's
            # argument only as a fallback. It used to be the argument alone, so
            # the analyzer's range was discarded and this was always "".
            reference_range=data.reference_range or reference_range,
            # Still the ingestion time, deliberately: changing what `timestamp`
            # means would silently reinterpret an existing field. The
            # instrument's own completion time is carried separately, unparsed,
            # because its format is vendor-specific and guessing one would be an
            # invention.
            timestamp=datetime.now(UTC),
            # IA-050: this was the literal "final" for every result. The bridge
            # performs no validation of any kind, so it cannot know a result is
            # final -- and "final" is the one direction in which being wrong is
            # unsafe. The instrument's own status is carried verbatim below; this
            # field now states what the bridge can actually attest.
            status="preliminary",
            device_abnormal_flags=data.abnormal_flags,
            device_nature_of_abnormality=nature_of_abnormality,
            device_result_status=data.result_status,
            device_completed_at=data.completed_at,
        )
