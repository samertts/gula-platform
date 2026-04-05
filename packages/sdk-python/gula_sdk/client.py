"""GULA SDK — GulaClient.

The single entry-point for any external system (LIS, HLIMS, hospital HIS,
government portal) to integrate with the GULA Platform.

Quick start::

    from gula_sdk import GulaClient

    client = GulaClient(
        base_url="https://gula.example.iq",
        api_key="sk-gula-...",
    )

    # Create a patient
    patient = client.create_patient(
        full_name="أحمد محمد علي",
        phone="07801234567",
        gender="M",
        date_of_birth="1990-05-15",
    )

    # Create a lab order
    order = client.create_order(
        patient_id=patient.id,
        test_type_ids=[1, 3, 7],   # CBC, LFT, RFT
        priority="urgent",
    )

    # Submit results (from analyser)
    result = client.submit_result(
        order_id=order.id,
        test_type_id=1,
        value="4.5",
        unit="x10³/μL",
    )

    # Submit an insurance claim
    claim = client.submit_claim(
        patient_id=patient.id,
        order_id=order.id,
        amount=25000,
        currency="IQD",
        insurance_id="INS-9981234",
    )

Integration in 10 minutes:
  - pip install gula-sdk
  - Copy your API key from the GULA admin dashboard
  - Point base_url at your GULA instance
  - Done — no config files, no XML, no HL7 parsing required
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from typing import Any, Optional
from urllib.parse import urljoin

import httpx

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

logger = logging.getLogger("gula_sdk")

_DEFAULT_TIMEOUT   = 30.0    # seconds
_DEFAULT_MAX_RETRY = 3
_RETRY_BACKOFF     = (1.0, 2.0, 4.0)   # exponential backoff per attempt
_RETRY_ON_STATUS   = {429, 500, 502, 503, 504}


class GulaClient:
    """
    GULA Platform API client.

    Thread-safe. Re-use a single instance across your application
    (connection pool is shared, idempotency keys are scoped per call).

    Args:
        base_url:     Full URL of your GULA instance (e.g. https://gula.example.iq).
                      Trailing slash is optional.
        api_key:      Bearer token from the GULA admin dashboard.
        lab_id:       Optional default lab_id to attach to every request.
                      Can be overridden per-call.
        timeout:      HTTP timeout in seconds (default 30).
        max_retries:  Retry attempts for transient failures (default 3).
        verify_ssl:   Whether to verify TLS certificates (default True).
                      Set False only for local/dev instances with self-signed certs.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        lab_id: Optional[int] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRY,
        verify_ssl: bool = True,
    ) -> None:
        self.base_url    = base_url.rstrip("/")
        self._api_key    = api_key
        self.lab_id      = lab_id
        self._timeout    = timeout
        self._max_retry  = max_retries
        self._verify_ssl = verify_ssl
        self._http       = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
                "Accept":        "application/json",
                "X-SDK-Version": "1.0.0",
                "X-SDK-Client":  "gula-sdk-python",
            },
            timeout=timeout,
            verify=verify_ssl,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "GulaClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ─── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _make_idempotency_key(*parts: Any) -> str:
        """Deterministic idempotency key derived from call inputs."""
        raw = ":".join(str(p) for p in parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """
        Execute an HTTP request with retry + error mapping.

        All GULA API errors are mapped to typed exceptions so callers
        can handle them precisely without parsing error strings.
        """
        url = path if path.startswith("http") else path
        headers: dict = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        last_exc: Exception = RuntimeError("no attempts made")

        for attempt in range(self._max_retry + 1):
            try:
                resp = self._http.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    headers=headers,
                )
            except httpx.TimeoutException as exc:
                last_exc = GulaNetworkError(f"Request timed out: {exc}")
                if attempt < self._max_retry:
                    time.sleep(_RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)])
                    continue
                raise last_exc from exc
            except httpx.RequestError as exc:
                last_exc = GulaNetworkError(f"Network error: {exc}")
                if attempt < self._max_retry:
                    time.sleep(_RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)])
                    continue
                raise last_exc from exc

            status = resp.status_code
            logger.debug("GULA API %s %s → %d (attempt %d)", method, path, status, attempt + 1)

            # Success
            if 200 <= status < 300:
                try:
                    return resp.json()
                except Exception:
                    return {"raw": resp.text}

            # Retriable errors
            if status in _RETRY_ON_STATUS and attempt < self._max_retry:
                wait = _RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)]
                if status == 429:
                    wait = float(resp.headers.get("Retry-After", wait))
                logger.warning("GULA API %d on %s — retry %d in %.0fs", status, path, attempt + 1, wait)
                time.sleep(wait)
                continue

            # Map errors to typed exceptions
            try:
                body = resp.json()
                detail = body.get("detail", "")
            except Exception:
                detail = resp.text

            if status == 401:
                raise GulaAuthError("Invalid or expired API key", status_code=401, detail=detail)
            if status == 404:
                raise GulaNotFoundError(f"Resource not found: {path}", status_code=404, detail=detail)
            if status == 409:
                raise GulaConflictError(f"Conflict: {detail}", status_code=409, detail=detail)
            if status == 422:
                errors = body.get("detail", []) if isinstance(body, dict) else []
                # Catch incompatible transfusion errors specifically
                detail_str = str(detail)
                if "INCOMPATIBLE" in detail_str or "⛔" in detail_str:
                    raise IncompatibleTransfusionError(detail_str, status_code=422)
                raise GulaValidationError(f"Validation failed: {detail}", errors=errors)
            if status == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                raise GulaRateLimitError("Rate limit exceeded", retry_after=retry_after)
            if status >= 500:
                raise GulaServerError(f"Server error {status}: {detail}", status_code=status)

            raise GulaError(f"Unexpected HTTP {status}: {detail}", status_code=status)

        raise last_exc  # type: ignore[misc]

    # ─── 1. Patients ──────────────────────────────────────────────────────────

    def create_patient(
        self,
        full_name: str,
        phone: str,
        gender: str,
        *,
        date_of_birth: Optional[str] = None,
        national_id: Optional[str] = None,
        blood_type: Optional[str] = None,
        lab_id: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> Patient:
        """
        Register a new patient.

        Args:
            full_name:    Patient's full name in Arabic or English.
            phone:        Iraqi mobile number (07xxxxxxxxx).
            gender:       "M" or "F".
            date_of_birth: ISO date string (YYYY-MM-DD), optional.
            national_id:  Iraqi National ID number, optional.
            blood_type:   e.g. "A+", "O-", optional.
            lab_id:       Override the client's default lab_id.
            idempotency_key: Prevent duplicate registration on retry.
                           If omitted, derived from (phone, full_name).

        Returns:
            Patient — the created patient record.

        Raises:
            GulaValidationError: phone format invalid, required field missing.
            GulaConflictError:   patient with this phone already exists.
            GulaAuthError:       API key not authorised for patient creation.
        """
        idem_key = idempotency_key or self._make_idempotency_key("patient", phone, full_name)
        body: dict = {
            "full_name":  full_name,
            "phone":      phone,
            "gender":     gender,
        }
        if date_of_birth:
            body["date_of_birth"] = date_of_birth
        if national_id:
            body["national_id"] = national_id
        if blood_type:
            body["blood_type"] = blood_type
        if lab_id or self.lab_id:
            body["lab_id"] = lab_id or self.lab_id

        raw = self._request("POST", "/patients/", json=body, idempotency_key=idem_key)
        return Patient.from_dict(raw)

    def get_patient(self, patient_id: int) -> Patient:
        """Fetch a patient by ID."""
        raw = self._request("GET", f"/patients/{patient_id}")
        return Patient.from_dict(raw)

    def find_patient_by_phone(self, phone: str) -> Optional[Patient]:
        """Search for a patient by phone number. Returns None if not found."""
        try:
            raw = self._request("GET", "/patients/", params={"phone": phone})
            items = raw if isinstance(raw, list) else raw.get("items", [])
            return Patient.from_dict(items[0]) if items else None
        except GulaNotFoundError:
            return None

    # ─── 2. Lab Orders ────────────────────────────────────────────────────────

    def create_order(
        self,
        patient_id: int,
        test_type_ids: list[int],
        *,
        priority: str = "routine",
        sample_type: Optional[str] = None,
        notes: Optional[str] = None,
        lab_id: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> LabOrder:
        """
        Create a lab order for a patient.

        Args:
            patient_id:     ID of the patient (from create_patient or get_patient).
            test_type_ids:  List of test type IDs to order.
            priority:       "routine" | "urgent" | "stat". Default: "routine".
            sample_type:    Override sample type (e.g. "whole_blood", "serum").
            notes:          Free-text clinical notes for the lab.
            lab_id:         Override the client's default lab_id.
            idempotency_key: Prevent duplicate orders on retry.

        Returns:
            LabOrder — the created order with its barcode.

        Raises:
            GulaValidationError: unknown test_type_id or invalid priority.
            GulaNotFoundError:   patient_id does not exist.
        """
        idem_key = idempotency_key or self._make_idempotency_key(
            "order", patient_id, sorted(test_type_ids), priority
        )
        body: dict = {
            "patient_id":    patient_id,
            "test_type_ids": test_type_ids,
            "priority":      priority,
        }
        if sample_type:
            body["sample_type"] = sample_type
        if notes:
            body["notes"] = notes
        if lab_id or self.lab_id:
            body["lab_id"] = lab_id or self.lab_id

        raw = self._request("POST", "/orders/", json=body, idempotency_key=idem_key)
        return LabOrder.from_dict(raw)

    def get_order(self, order_id: int) -> LabOrder:
        """Fetch a lab order by ID."""
        raw = self._request("GET", f"/orders/{order_id}")
        return LabOrder.from_dict(raw)

    def list_orders(
        self,
        patient_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[LabOrder]:
        """List lab orders with optional filters."""
        params: dict = {"limit": limit}
        if patient_id:
            params["patient_id"] = patient_id
        if status:
            params["status"] = status
        raw = self._request("GET", "/orders/", params=params)
        items = raw if isinstance(raw, list) else raw.get("items", [])
        return [LabOrder.from_dict(item) for item in items]

    # ─── 3. Results ───────────────────────────────────────────────────────────

    def submit_result(
        self,
        order_id: int,
        test_type_id: int,
        value: str,
        *,
        unit: Optional[str] = None,
        reference_range: Optional[str] = None,
        notes: Optional[str] = None,
        device_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> LabResult:
        """
        Submit a result from a lab analyser.

        This is the core integration point for LIS systems:
          1. Analyser produces result (e.g. Hb = 12.5 g/dL)
          2. LIS calls submit_result()
          3. GULA stores, validates, interprets, and notifies

        Args:
            order_id:        The lab order this result belongs to.
            test_type_id:    Which test type this result is for.
            value:           Numeric or text result value (always pass as string).
            unit:            Result unit (e.g. "g/dL", "x10³/μL").
            reference_range: e.g. "13.0-17.0" (overrides test type default).
            notes:           Analyser-generated comments or flags.
            device_id:       Analyser serial number for traceability.
            idempotency_key: Prevent duplicate result submission on retry.

        Returns:
            LabResult — stored result with GULA's interpretation.

        Raises:
            GulaValidationError: value format not acceptable for this test type.
            GulaNotFoundError:   order_id or test_type_id does not exist.
            GulaConflictError:   result for this (order, test_type) already exists.
        """
        idem_key = idempotency_key or self._make_idempotency_key(
            "result", order_id, test_type_id, value
        )
        body: dict = {
            "order_id":     order_id,
            "test_type_id": test_type_id,
            "value":        str(value),
        }
        if unit:
            body["unit"] = unit
        if reference_range:
            body["reference_range"] = reference_range
        if notes:
            body["notes"] = notes
        if device_id:
            body["device_id"] = device_id

        raw = self._request("POST", "/results/", json=body, idempotency_key=idem_key)
        return LabResult.from_dict(raw)

    def get_result(self, result_id: int) -> LabResult:
        """Fetch a single result by ID."""
        raw = self._request("GET", f"/results/{result_id}")
        return LabResult.from_dict(raw)

    def list_results(self, order_id: int) -> list[LabResult]:
        """List all results for a lab order."""
        raw = self._request("GET", "/results/", params={"order_id": order_id})
        items = raw if isinstance(raw, list) else raw.get("items", [])
        return [LabResult.from_dict(item) for item in items]

    # ─── 4. Claims ────────────────────────────────────────────────────────────

    def submit_claim(
        self,
        patient_id: int,
        order_id: int,
        amount: float,
        *,
        currency: str = "IQD",
        insurance_id: Optional[str] = None,
        diagnosis_codes: Optional[list[str]] = None,
        notes: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Claim:
        """
        Submit an insurance claim for a completed lab order.

        GULA runs automatic fraud scoring on every claim.
        Check claim.fraud_decision ("approve" | "review" | "reject")
        before processing payment.

        Args:
            patient_id:       The patient ID.
            order_id:         The completed lab order ID.
            amount:           Claim amount (must be > 0).
            currency:         ISO currency code. Default: "IQD".
            insurance_id:     Patient's insurance card number.
            diagnosis_codes:  ICD-10 codes (e.g. ["E11.9", "I10"]).
            notes:            Clinical notes for the insurer.
            idempotency_key:  Prevent duplicate claim submission.

        Returns:
            Claim — with fraud_score and fraud_decision populated.

        Raises:
            GulaValidationError: amount ≤ 0, invalid currency.
            GulaConflictError:   claim for this order already exists.
        """
        idem_key = idempotency_key or self._make_idempotency_key(
            "claim", patient_id, order_id, amount, currency
        )
        body: dict = {
            "patient_id": patient_id,
            "order_id":   order_id,
            "amount":     amount,
            "currency":   currency,
        }
        if insurance_id:
            body["insurance_id"] = insurance_id
        if diagnosis_codes:
            body["diagnosis_codes"] = diagnosis_codes
        if notes:
            body["notes"] = notes

        raw = self._request("POST", "/claims/", json=body, idempotency_key=idem_key)
        return Claim.from_dict(raw)

    def get_claim(self, claim_id: int) -> Claim:
        """Fetch a claim by ID."""
        raw = self._request("GET", f"/claims/{claim_id}")
        return Claim.from_dict(raw)

    # ─── 5. Blood Network (GBN) ───────────────────────────────────────────────

    def register_donor(
        self,
        full_name: str,
        blood_type: str,
        phone: str,
        gender: str,
        *,
        date_of_birth: Optional[str] = None,
        national_id: Optional[str] = None,
        lab_id: Optional[int] = None,
    ) -> BloodDonor:
        """Register a blood donor."""
        body: dict = {
            "full_name":  full_name,
            "blood_type": blood_type,
            "phone":      phone,
            "gender":     gender,
        }
        if date_of_birth:
            body["date_of_birth"] = date_of_birth
        if national_id:
            body["national_id"] = national_id
        if lab_id or self.lab_id:
            body["lab_id"] = lab_id or self.lab_id

        raw = self._request("POST", "/gbn/donors", json=body)
        return BloodDonor.from_dict(raw)

    def get_inventory(self, lab_id: Optional[int] = None) -> InventorySummary:
        """Get blood inventory summary for a lab or the full network."""
        params: dict = {}
        if lab_id or self.lab_id:
            params["lab_id"] = lab_id or self.lab_id

        summary = self._request("GET", "/gbn/inventory/summary", params=params)
        shortages = self._request("GET", "/gbn/inventory/shortages", params=params)

        return InventorySummary.from_dict({"summary": summary, "shortages": shortages})

    def search_blood_network(
        self,
        blood_type: str,
        component: str,
        units_needed: int,
    ) -> ApiResponse:
        """Search the national blood network for available units."""
        raw = self._request(
            "GET",
            "/gbn/network/search",
            params={
                "blood_type":   blood_type,
                "component":    component,
                "units_needed": units_needed,
            },
        )
        return ApiResponse(data=raw)

    # ─── 6. Health check ──────────────────────────────────────────────────────

    def health(self) -> dict:
        """
        Check GULA platform health.

        Returns dict with at least {"status": "ok"} on success.
        Raises GulaServerError if the platform is degraded.
        """
        return self._request("GET", "/health")

    def ping(self) -> bool:
        """Quick connectivity check. Returns True if GULA is reachable."""
        try:
            h = self.health()
            return h.get("status") in ("ok", "degraded")
        except (GulaNetworkError, GulaServerError):
            return False
