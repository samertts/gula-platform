"""GULA SDK — Python client for the GULA Laboratory Platform.

Integration in 10 minutes::

    pip install gula-sdk

    from gula_sdk import GulaClient

    with GulaClient(base_url="https://gula.example.iq", api_key="sk-gula-...") as client:
        patient = client.create_patient(
            full_name="أحمد محمد علي",
            phone="07801234567",
            gender="M",
        )
        order = client.create_order(patient_id=patient.id, test_type_ids=[1, 3])
        result = client.submit_result(order_id=order.id, test_type_id=1, value="4.5", unit="x10³/μL")
"""

from .client import GulaClient
from .exceptions import (
    GulaAuthError,
    GulaConflictError,
    GulaError,
    GulaNetworkError,
    GulaNotFoundError,
    GulaRateLimitError,
    GulaServerError,
    GulaValidationError,
    IncompatibleTransfusionError,
)
from .models import (
    ApiResponse,
    BloodDonor,
    Claim,
    InventorySummary,
    LabOrder,
    LabResult,
    Patient,
)

__version__ = "1.0.0"
__author__  = "GULA Platform"
__all__ = [
    "GulaClient",
    # Exceptions
    "GulaError",
    "GulaAuthError",
    "GulaValidationError",
    "GulaNotFoundError",
    "GulaConflictError",
    "GulaRateLimitError",
    "GulaServerError",
    "GulaNetworkError",
    "IncompatibleTransfusionError",
    # Models
    "Patient",
    "LabOrder",
    "LabResult",
    "Claim",
    "BloodDonor",
    "InventorySummary",
    "ApiResponse",
]
