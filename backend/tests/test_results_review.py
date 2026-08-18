from types import SimpleNamespace

import pytest

from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.clinical_gateway.results_review_routes import router
from app.clinical_gateway.results_review_service import ResultsReviewService


def test_results_review_route_is_canonical():
    paths = {route.path for route in router.routes}
    assert "/api/v1/clinical/orders/{order_id}/results/{result_id}/review" in paths


def test_result_review_dto_excludes_secret_fields():
    result = SimpleNamespace(
        id=1,
        order_id=2,
        test_name="Glucose",
        value=95.0,
        value_text=None,
        unit="mg/dL",
        flag="normal",
        review_status="ACCEPTED",
        reviewed_by="practitioner-1",
        reviewed_at=None,
        review_note="checked",
        version=2,
        token="must-not-leak",
        result_link="must-not-leak",
    )
    dto = ResultsReviewService.to_safe_dict(result)
    assert "token" not in dto
    assert "result_link" not in dto
    assert dto["review_status"] == "ACCEPTED"


def test_review_service_rejects_invalid_decision_before_db():
    access = SimpleNamespace(require_operation=lambda operation: None)
    with pytest.raises(ClinicalGatewayBlocked, match="invalid_result_review_decision"):
        ResultsReviewService(db=None).review(
            access=access,
            order_id=1,
            result_id=1,
            expected_version=1,
            decision="CLIENT_CONTROLLED",
        )
