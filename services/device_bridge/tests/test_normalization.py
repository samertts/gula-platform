from app.pipeline.normalizer import Normalizer
from app.pipeline.parser_engine import ParsedResult


def test_normalize_result_maps_hb_to_hemoglobin() -> None:
    parsed = ParsedResult(test_code="Hb", value=13.5, unit="g/dL")
    normalized = Normalizer().transform(parsed, patient_id="P1", device_id="CBC-01")

    assert normalized.test_name == "Hemoglobin"
    # IA-050. This asserted "final", which encoded the defect as the contract:
    # the bridge stamped every analyzer result as a final, verified result while
    # performing no validation at all. What it can attest is "preliminary"; the
    # instrument's own status is carried separately in device_result_status.
    assert normalized.status == "preliminary"
    assert normalized.device_result_status == "", (
        "this ParsedResult carries no device status, so none may be invented"
    )
