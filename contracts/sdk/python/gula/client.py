from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .exceptions import map_status_code
from .models import (
    ActingAppoint,
    AnalyzeRequest,
    BatchOrderRequest,
    CalibrationRecordRequest,
    ChangePasswordRequest,
    ChangeRoleRequest,
    ChatRequest,
    CheckResponse,
    CitizenLoginRequest,
    CitizenRegisterRequest,
    ClaimCreate,
    ClaimResponse,
    CreateEmployeeRequest,
    CreateLabRequest,
    CreateOrderRequest,
    CreateUserRequest,
    DelegationCreate,
    DemandSignalBody,
    DeviceMessageRequest,
    DeviceSubmission,
    DeviceTokenRequest,
    DoctorRegisterRequest,
    FeatureFlagBody,
    FeedbackIn,
    GrantRequest,
    GrantResponse,
    HeartbeatRequest,
    HeartbeatResponse,
    InstrumentCreateRequest,
    InteractionIn,
    InteractionOut,
    InventoryRequest,
    IQCRunRequest,
    KillSwitchRequest,
    LabRegister,
    LabUpdate,
    LinkIdentityRequest,
    LoginRequest,
    MaintenanceRecordRequest,
    MergeRequest,
    MergeResponse,
    ModelAssignRequest,
    ModelRegisterRequest,
    ModelStatusUpdate,
    NationalIdRequest,
    NodeCreate,
    NotifyRequest,
    PatientCreate,
    PatientUpdate,
    PendingReviewPage,
    PolicyUpdate,
    PolicyView,
    QCSubmit,
    RefreshRequest,
    RegisterDeviceRequest,
    RegisterDeviceResponse,
    RejectRequest,
    ReportGenerateRequest,
    ResolveDecision,
    ResolveRequest,
    ResolveResponse,
    ResultCreateRequest,
    ResultValidateRequest,
    RevokeRequest,
    RevokeResponse,
    SampleCreate,
    SampleUpdate,
    ScanRequest,
    SetTierBody,
    SpecimenRegisterRequest,
    SpecimenTransitionRequest,
    StaffRegisterRequest,
    SuggestRequest,
    TaskResultRequest,
    TaskSubmitRequest,
    TestResultCreate,
    TestResultValidateRequest,
    UnresolvedIn,
    UpdateEmployeeRequest,
    UpgradeRequestBody,
    WorkerCreate,
)

logger = logging.getLogger("gula")

_RETRYABLE = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3


class GulaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: str | None = None,
        timeout: float = 30.0,
        max_retries: int = _MAX_RETRIES,
    ):
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> GulaClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def set_token(self, token: str) -> None:
        self._token = token

    # ── Internal request helpers ──────────────────────────────────────────────

    def _build_headers(
        self, idempotency_key: str | None = None
    ) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._build_headers(idempotency_key)
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=query,
                    json=body,
                )

                if attempt > 1:
                    logger.info("Retry attempt %d/%d for %s %s", attempt, self._max_retries, method, path)

                if response.is_success:
                    if response.status_code == 204:
                        return None
                    ct = response.headers.get("content-type", "")
                    if "application/json" in ct:
                        return response.json()
                    return response.text

                if response.status_code in _RETRYABLE and attempt < self._max_retries:
                    backoff = 2 ** attempt
                    logger.warning(
                        "HTTP %d on %s %s, retrying in %ds (attempt %d/%d)",
                        response.status_code,
                        method,
                        path,
                        backoff,
                        attempt,
                        self._max_retries,
                    )
                    await asyncio.sleep(backoff)
                    continue

                raise map_status_code(
                    response.status_code,
                    self._try_decode(response),
                )

            except httpx.TimeoutException as e:
                last_exc = e
                if attempt < self._max_retries:
                    backoff = 2 ** attempt
                    logger.warning("Timeout on %s %s, retrying in %ds", method, path, backoff)
                    await asyncio.sleep(backoff)
                    continue
                raise

            except httpx.TransportError as e:
                last_exc = e
                if attempt < self._max_retries:
                    backoff = 2 ** attempt
                    logger.warning("Transport error on %s %s, retrying in %ds", method, path, backoff)
                    await asyncio.sleep(backoff)
                    continue
                raise

        if last_exc:
            raise last_exc

        return None

    @staticmethod
    def _try_decode(response: httpx.Response) -> dict | None:
        try:
            return response.json()
        except Exception:
            return None

    async def _get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, query=query)

    async def _post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        return await self._request("POST", path, body=body, idempotency_key=idempotency_key)

    async def _put(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return await self._request("PUT", path, body=body)

    async def _patch(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return await self._request("PATCH", path, body=body)

    async def _delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> dict:
        return await self._post("/login", LoginRequest(email=email, password=password).model_dump())

    async def refresh_token(self, refresh_token: str | None = None) -> dict:
        return await self._post("/auth/refresh", RefreshRequest(refresh_token=refresh_token).model_dump())

    async def change_password(self, current_password: str, new_password: str) -> dict:
        return await self._post(
            "/auth/change-password",
            ChangePasswordRequest(current_password=current_password, new_password=new_password).model_dump(),
        )

    async def citizen_login(self, identifier: str, password: str) -> dict:
        return await self._post(
            "/citizen/login",
            CitizenLoginRequest(identifier=identifier, password=password).model_dump(),
        )

    # ── Registration ──────────────────────────────────────────────────────────

    async def register_lab(
        self,
        lab_name: str,
        admin_name: str,
        email: str,
        password: str,
        **kwargs: Any,
    ) -> dict:
        body = LabRegisterRequest(
            lab_name=lab_name, admin_name=admin_name, email=email, password=password, **kwargs
        )
        return await self._post("/register", body.model_dump())

    async def register_citizen(
        self,
        full_name: str,
        phone: str,
        password: str,
        **kwargs: Any,
    ) -> dict:
        body = CitizenRegisterRequest(full_name=full_name, phone=phone, password=password, **kwargs)
        return await self._post("/register/citizen", body.model_dump())

    async def register_staff(
        self,
        name: str,
        email: str,
        password: str,
        **kwargs: Any,
    ) -> dict:
        body = StaffRegisterRequest(name=name, email=email, password=password, **kwargs)
        return await self._post("/register/staff", body.model_dump())

    async def register_doctor(
        self,
        full_name: str,
        email: str,
        phone: str,
        password: str,
        license_number: str,
        **kwargs: Any,
    ) -> dict:
        body = DoctorRegisterRequest(
            full_name=full_name,
            email=email,
            phone=phone,
            password=password,
            license_number=license_number,
            **kwargs,
        )
        return await self._post("/register/doctor", body.model_dump())

    # ── National ID ───────────────────────────────────────────────────────────

    async def verify_national_id(self, national_id: str) -> dict:
        return await self._post("/national-id/verify", NationalIdRequest(national_id=national_id).model_dump())

    # ── Identity ──────────────────────────────────────────────────────────────

    async def link_identity(
        self, patient_id: int, national_id: str, confirm_name: str | None = None
    ) -> dict:
        return await self._post(
            "/identity/link",
            LinkIdentityRequest(patient_id=patient_id, national_id=national_id, confirm_name=confirm_name).model_dump(),
        )

    async def verify_identity_status(self) -> dict:
        return await self._get("/identity/verify")

    async def verify_identity_document(self) -> dict:
        return await self._post("/identity/verify")

    # ── Mobile ────────────────────────────────────────────────────────────────

    async def register_device(self, device_token: str, platform: str, **kwargs: Any) -> dict:
        body = DeviceTokenRequest(device_token=device_token, platform=platform, **kwargs)
        return await self._post("/mobile/register-device", body.model_dump())

    # ── Health ────────────────────────────────────────────────────────────────

    async def health(self) -> dict:
        return await self._get("/health")

    async def health_live(self) -> dict:
        return await self._get("/health/live")

    async def health_ready(self) -> dict:
        return await self._get("/health/ready")

    async def health_status(self) -> dict:
        return await self._get("/health/status")

    async def health_deep(self) -> dict:
        return await self._get("/health/deep")

    # ── Patients ──────────────────────────────────────────────────────────────

    async def list_patients(
        self,
        page: int = 1,
        limit: int = 50,
        **filters: Any,
    ) -> dict:
        query = {"page": page, "limit": limit, **filters}
        return await self._get("/patients", query=query)

    async def create_patient(self, patient: PatientCreate) -> dict:
        return await self._post("/patients", patient.model_dump())

    async def get_patient(self, patient_id: int) -> dict:
        return await self._get(f"/patients/{patient_id}")

    async def update_patient(self, patient_id: int, update: PatientUpdate) -> dict:
        return await self._put(f"/patients/{patient_id}", update.model_dump(exclude_none=True))

    async def delete_patient(self, patient_id: int) -> None:
        await self._delete(f"/patients/{patient_id}")

    async def search_patients(self, query: str, page: int = 1, limit: int = 50) -> dict:
        return await self._get("/patients/search", query={"q": query, "page": page, "limit": limit})

    async def merge_patients(self, patient_id: int, target_id: int) -> dict:
        return await self._put(f"/patients/{patient_id}/merge", {"target_id": target_id})

    async def patient_history(self, patient_id: int, page: int = 1, limit: int = 50) -> dict:
        return await self._get(f"/patients/{patient_id}/history", query={"page": page, "limit": limit})

    async def patients_stats(self) -> dict:
        return await self._get("/patients/stats")

    async def patients_activity(self, page: int = 1, limit: int = 50) -> dict:
        return await self._get("/patients/activity", query={"page": page, "limit": limit})

    async def lookup_patient_by_phone(self, phone: str) -> dict:
        return await self._get(f"/patients/phone/{phone}")

    async def export_patients_csv(self) -> Any:
        return await self._get("/patients/export-csv")

    async def bulk_assign_lab(self, patient_ids: list[int], lab_id: int) -> dict:
        return await self._post("/patients/bulk-assign-lab", {"patient_ids": patient_ids, "lab_id": lab_id})

    async def convert_guest_patient(self, patient_id: int) -> dict:
        return await self._post("/patients/convert-guest", {"patient_id": patient_id})

    async def patient_card_scan(self, token: str) -> dict:
        return await self._post("/patient-card/scan", ScanRequest(token=token).model_dump())

    # ── Labs ──────────────────────────────────────────────────────────────────

    async def list_labs(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        query = {"page": page, "limit": limit, **filters}
        return await self._get("/labs", query=query)

    async def create_lab(self, request: CreateLabRequest) -> dict:
        return await self._post("/labs", request.model_dump())

    async def get_lab(self, lab_id: int) -> dict:
        return await self._get(f"/labs/{lab_id}")

    async def update_lab(self, lab_id: int, update: LabUpdate) -> dict:
        return await self._put(f"/labs/{lab_id}", update.model_dump(exclude_none=True))

    async def delete_lab(self, lab_id: int) -> None:
        await self._delete(f"/labs/{lab_id}")

    async def search_labs(self, query: str, page: int = 1, limit: int = 50) -> dict:
        return await self._get("/labs/search", query={"q": query, "page": page, "limit": limit})

    async def nearby_labs(self, lat: float, lng: float, radius_km: float = 10) -> dict:
        return await self._get("/labs/nearby", query={"lat": lat, "lng": lng, "radius_km": radius_km})

    async def available_labs(self) -> dict:
        return await self._get("/labs/available")

    async def lab_registration_types(self) -> dict:
        return await self._get("/labs/registration-types")

    async def shared_labs(self, page: int = 1, limit: int = 50) -> dict:
        return await self._get("/labs/shared-labs", query={"page": page, "limit": limit})

    async def labs_map_data(self) -> dict:
        return await self._get("/labs/map-data")

    async def get_lab_stats(self, lab_id: int) -> dict:
        return await self._get(f"/labs/{lab_id}/stats")

    async def get_lab_work_hours(self, lab_id: int) -> dict:
        return await self._get(f"/labs/{lab_id}/work-hours")

    async def update_lab_work_hours(self, lab_id: int, hours: dict) -> dict:
        return await self._put(f"/labs/{lab_id}/work-hours", hours)

    async def update_lab_settings(self, lab_id: int, settings: dict) -> dict:
        return await self._put(f"/labs/{lab_id}/settings", settings)

    async def get_lab_logo(self, lab_id: int) -> Any:
        return await self._get(f"/labs/{lab_id}/logo")

    async def upload_lab_logo(self, lab_id: int, file_bytes: bytes, filename: str) -> dict:
        url = f"{self.base_url}/labs/{lab_id}/logo"
        headers = self._build_headers()
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, files={"file": (filename, file_bytes)})
            if not resp.is_success:
                raise map_status_code(resp.status_code, self._try_decode(resp))
            return resp.json()

    # ── Lab Employees ─────────────────────────────────────────────────────────

    async def list_employees(self, lab_id: int, page: int = 1, limit: int = 50) -> dict:
        return await self._get(f"/labs/{lab_id}/users", query={"page": page, "limit": limit})

    async def create_employee(self, request: CreateEmployeeRequest) -> dict:
        return await self._post("/labs/me/employees", request.model_dump())

    async def update_employee(self, employee_id: int, update: UpdateEmployeeRequest) -> dict:
        return await self._put(f"/labs/me/employees/{employee_id}", update.model_dump(exclude_none=True))

    # ── Orders ────────────────────────────────────────────────────────────────

    async def create_order(self, request: CreateOrderRequest, idempotency_key: str | None = None) -> dict:
        return await self._post("/orders", request.model_dump(), idempotency_key=idempotency_key)

    async def list_orders(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        return await self._get("/orders", query={"page": page, "limit": limit, **filters})

    async def get_order(self, order_id: int) -> dict:
        return await self._get(f"/orders/{order_id}")

    async def update_order(self, order_id: int, data: dict) -> dict:
        return await self._put(f"/orders/{order_id}", data)

    async def delete_order(self, order_id: int) -> None:
        await self._delete(f"/orders/{order_id}")

    async def batch_create_orders(self, request: BatchOrderRequest) -> dict:
        return await self._post("/batch/orders", request.model_dump())

    async def analyze_results(self, request: AnalyzeRequest) -> dict:
        return await self._post("/analyze", request.model_dump())

    # ── Results ───────────────────────────────────────────────────────────────

    async def list_results(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        return await self._get("/results", query={"page": page, "limit": limit, **filters})

    async def create_result(self, result: dict) -> dict:
        return await self._post("/results", result)

    async def get_result(self, result_id: int) -> dict:
        return await self._get(f"/results/{result_id}")

    async def update_result(self, result_id: int, data: dict) -> dict:
        return await self._put(f"/results/{result_id}", data)

    async def delete_result(self, result_id: int) -> None:
        await self._delete(f"/results/{result_id}")

    async def bulk_create_results(self, results: list[dict]) -> dict:
        return await self._post("/results/bulk", {"results": results})

    async def verify_result(self, result_id: int) -> dict:
        return await self._put(f"/results/{result_id}/verify")

    async def approve_result(self, result_id: int) -> dict:
        return await self._put(f"/results/{result_id}/approve")

    async def validate_result(self, result_id: int) -> dict:
        return await self._put(f"/results/{result_id}/validate")

    async def auto_validate_results(self) -> dict:
        return await self._post("/results/auto-validate")

    async def amend_result(self, result_id: int, data: dict) -> dict:
        return await self._post(f"/results/{result_id}/amend", data)

    async def get_result_amendments(self, result_id: int, page: int = 1, limit: int = 50) -> dict:
        return await self._get(f"/results/{result_id}/amendments", query={"page": page, "limit": limit})

    async def results_stats(self) -> dict:
        return await self._get("/results/stats")

    async def print_result(self, result_id: int) -> dict:
        return await self._post(f"/results/{result_id}/print")

    async def send_result_to_patient(self, result_id: int, channel: str = "whatsapp") -> dict:
        return await self._post("/results/send-to-patient", {"result_id": result_id, "channel": channel})

    async def result_timeline(self, result_id: int) -> dict:
        return await self._get(f"/results/{result_id}/timeline")

    async def flag_result_critical(self, result_id: int) -> dict:
        return await self._post(f"/results/{result_id}/flag-critical")

    async def generate_result_report(self, result_id: int) -> dict:
        return await self._post(f"/results/{result_id}/report")

    async def list_result_reports(self, page: int = 1, limit: int = 50) -> dict:
        return await self._get("/results/reports", query={"page": page, "limit": limit})

    # ── Test Results (Citizen-centric) ────────────────────────────────────────

    async def create_test_result(self, result: TestResultCreate, idempotency_key: str | None = None) -> dict:
        return await self._post("/test-results", result.model_dump(), idempotency_key=idempotency_key)

    async def list_test_results(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        return await self._get("/test-results", query={"page": page, "limit": limit, **filters})

    async def get_test_result(self, result_id: int) -> dict:
        return await self._get(f"/test-results/{result_id}")

    async def update_test_result(self, result_id: int, data: dict) -> dict:
        return await self._put(f"/test-results/{result_id}", data)

    async def delete_test_result(self, result_id: int) -> None:
        await self._delete(f"/test-results/{result_id}")

    async def get_test_results_by_citizen(self, health_id: str) -> dict:
        return await self._get(f"/test-results/citizen/{health_id}")

    async def test_result_stats(self) -> dict:
        return await self._get("/test-results/stats")

    async def validate_test_result(self, request: TestResultValidateRequest) -> dict:
        return await self._post("/test-results/validate", request.model_dump())

    async def bulk_approve_test_results(self, ids: list[int]) -> dict:
        return await self._post("/test-results/bulk-approve", {"ids": ids})

    async def export_test_result_pdf(self, result_id: int) -> Any:
        return await self._get(f"/test-results/export-pdf/{result_id}")

    async def import_test_results_csv(self, csv_bytes: bytes, filename: str) -> dict:
        url = f"{self.base_url}/test-results/import-csv"
        headers = self._build_headers()
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, files={"file": (filename, csv_bytes)})
            if not resp.is_success:
                raise map_status_code(resp.status_code, self._try_decode(resp))
            return resp.json()

    # ── Device Results ────────────────────────────────────────────────────────

    async def submit_device_results(self, submission: DeviceSubmission) -> dict:
        return await self._post("/device/results", submission.model_dump())

    # ── Samples ───────────────────────────────────────────────────────────────

    async def list_samples(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        return await self._get("/samples", query={"page": page, "limit": limit, **filters})

    async def create_sample(self, sample: SampleCreate) -> dict:
        return await self._post("/samples", sample.model_dump())

    async def get_sample(self, sample_id: int) -> dict:
        return await self._get(f"/samples/{sample_id}")

    async def update_sample(self, sample_id: int, update: SampleUpdate) -> dict:
        return await self._put(f"/samples/{sample_id}", update.model_dump(exclude_none=True))

    async def delete_sample(self, sample_id: int) -> None:
        await self._delete(f"/samples/{sample_id}")

    async def receive_sample(self, sample_id: int) -> dict:
        return await self._post(f"/samples/{sample_id}/receive")

    async def reject_sample(self, sample_id: int, reason: str) -> dict:
        return await self._post(f"/samples/{sample_id}/reject", {"reason": reason})

    async def sample_stats(self) -> dict:
        return await self._get("/samples/stats")

    async def export_samples(self) -> Any:
        return await self._get("/samples/export")

    async def bulk_register_samples(self, samples: list[dict]) -> dict:
        return await self._post("/samples/bulk-register", {"samples": samples})

    async def print_sample_barcode(self, sample_id: int) -> Any:
        return await self._get(f"/samples/{sample_id}/print-barcode")

    async def lookup_sample_by_barcode(self, barcode: str) -> dict:
        return await self._get(f"/samples/barcode/{barcode}")

    async def print_sample_label(self, sample_id: int) -> dict:
        return await self._post(f"/samples/{sample_id}/print-label")

    async def transfer_sample(self, sample_id: int, target_lab_id: int) -> dict:
        return await self._post(f"/samples/{sample_id}/transfer", {"target_lab_id": target_lab_id})

    async def sample_timeline(self, sample_id: int) -> dict:
        return await self._get(f"/samples/{sample_id}/timeline")

    async def sample_history(self, sample_id: int, page: int = 1, limit: int = 50) -> dict:
        return await self._get(f"/samples/history/{sample_id}", query={"page": page, "limit": limit})

    # ── Admin ─────────────────────────────────────────────────────────────────

    async def admin_create_lab(self, request: CreateLabRequest) -> dict:
        return await self._post("/admin/labs", request.model_dump())

    async def admin_list_labs(self, page: int = 1, limit: int = 50) -> dict:
        return await self._get("/admin/labs", query={"page": page, "limit": limit})

    async def admin_create_user(self, request: CreateUserRequest) -> dict:
        return await self._post("/admin/users", request.model_dump())

    async def admin_change_role(self, user_id: int, role: str, province_id: int | None = None) -> dict:
        return await self._put(
            f"/admin/users/{user_id}/role",
            ChangeRoleRequest(role=role, province_id=province_id).model_dump(),
        )

    async def admin_kill_switch(self, reason: str | None = None) -> dict:
        return await self._post("/admin/kill-switch", KillSwitchRequest(reason=reason).model_dump())

    async def admin_set_tier(self, lab_id: int, body: SetTierBody) -> dict:
        return await self._post(f"/admin/tiers/{lab_id}", body.model_dump())

    async def admin_set_feature_flag(self, lab_id: int, body: FeatureFlagBody) -> dict:
        return await self._post(f"/admin/tiers/flags/{lab_id}", body.model_dump())

    # ── Consent ───────────────────────────────────────────────────────────────

    async def grant_consent(self, request: GrantRequest) -> GrantResponse:
        data = await self._post("/consent/grant", request.model_dump())
        return GrantResponse(**data)

    async def revoke_consent(self, request: RevokeRequest) -> RevokeResponse:
        data = await self._post("/consent/revoke", request.model_dump())
        return RevokeResponse(**data)

    async def check_consent(self, gpid: str, grantee_id: str, scope: str) -> CheckResponse:
        data = await self._post("/consent/check", {"gpid": gpid, "grantee_id": grantee_id, "scope": scope})
        return CheckResponse(**data)

    # ── Claims ────────────────────────────────────────────────────────────────

    async def create_claim(self, claim: ClaimCreate, idempotency_key: str | None = None) -> ClaimResponse:
        key = idempotency_key or claim.idempotency_key
        data = await self._post("/claims", claim.model_dump(), idempotency_key=key)
        return ClaimResponse(**data)

    async def list_claims(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        return await self._get("/claims", query={"page": page, "limit": limit, **filters})

    async def get_claim(self, claim_id: int) -> dict:
        return await self._get(f"/claims/{claim_id}")

    async def submit_claim(self, claim_id: int) -> dict:
        return await self._post(f"/claims/{claim_id}/submit")

    async def validate_claim(self, claim_id: int) -> dict:
        return await self._post(f"/claims/{claim_id}/validate")

    # ── Edge ─────────────────────────────────────────────────────────────────

    async def edge_register_device(self, request: RegisterDeviceRequest) -> RegisterDeviceResponse:
        data = await self._post("/edge/devices/register", request.model_dump())
        return RegisterDeviceResponse(**data)

    async def edge_list_devices(self, page: int = 1, limit: int = 50) -> dict:
        return await self._get("/edge/devices", query={"page": page, "limit": limit})

    async def edge_get_device(self, device_id: str) -> dict:
        return await self._get(f"/edge/devices/{device_id}")

    async def edge_list_tasks(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        return await self._get("/edge/tasks", query={"page": page, "limit": limit, **filters})

    async def edge_submit_task(self, request: TaskSubmitRequest) -> dict:
        return await self._post("/edge/tasks", request.model_dump())

    async def edge_get_task(self, task_uid: str) -> dict:
        return await self._get(f"/edge/tasks/{task_uid}")

    async def edge_cancel_task(self, task_uid: str) -> dict:
        return await self._post(f"/edge/tasks/{task_uid}/cancel")

    async def edge_get_policy(self) -> PolicyView:
        data = await self._get("/edge/policy")
        return PolicyView(**data)

    async def edge_update_policy(self, update: PolicyUpdate) -> PolicyView:
        data = await self._put("/edge/policy", update.model_dump(exclude_none=True))
        return PolicyView(**data)

    async def edge_agent_heartbeat(self, request: HeartbeatRequest) -> HeartbeatResponse:
        data = await self._post("/edge/agent/heartbeat", request.model_dump())
        return HeartbeatResponse(**data)

    async def edge_agent_report_result(self, task_uid: str, request: TaskResultRequest) -> dict:
        return await self._post(f"/edge/agent/tasks/{task_uid}/result", request.model_dump())

    async def edge_register_model(self, request: ModelRegisterRequest) -> dict:
        return await self._post("/edge/models", request.model_dump())

    async def edge_update_model_status(self, model_uid: str, update: ModelStatusUpdate) -> dict:
        return await self._post(f"/edge/models/{model_uid}/status", update.model_dump())

    async def edge_assign_model(self, model_uid: str, request: ModelAssignRequest) -> dict:
        return await self._post(f"/edge/models/{model_uid}/assign", request.model_dump())

    # ── MPI ───────────────────────────────────────────────────────────────────

    async def mpi_resolve(self, request: ResolveRequest) -> ResolveResponse:
        data = await self._post("/mpi/resolve", request.model_dump())
        return ResolveResponse(**data)

    async def mpi_get_citizen(self, citizen_ulid: str) -> dict:
        return await self._get(f"/mpi/citizens/{citizen_ulid}")

    async def mpi_merge(self, request: MergeRequest) -> MergeResponse:
        data = await self._post("/mpi/merge", request.model_dump())
        return MergeResponse(**data)

    async def mpi_pending_review(self, page: int = 1, limit: int = 50) -> PendingReviewPage:
        data = await self._get("/mpi/review", query={"page": page, "limit": limit})
        return PendingReviewPage(**data)

    async def mpi_decide(self, claim_id: int, decision: ResolveDecision) -> dict:
        return await self._post(f"/mpi/review/{claim_id}/decide", decision.model_dump())

    # ── Notifications ─────────────────────────────────────────────────────────

    async def send_notification(self, request: NotifyRequest) -> dict:
        return await self._post("/notify/send", request.model_dump())

    async def list_notifications(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        return await self._get("/notifications", query={"page": page, "limit": limit, **filters})

    async def mark_notification_read(self, notification_id: int) -> dict:
        return await self._put(f"/notifications/{notification_id}/read")

    async def mark_all_notifications_read(self) -> dict:
        return await self._post("/notifications/read-all")

    # ── Quality Control ───────────────────────────────────────────────────────

    async def qc_submit(self, measurement: QCSubmit) -> dict:
        return await self._post("/qc/submit", measurement.model_dump())

    async def qc_batch_submit(self, measurements: list[QCSubmit]) -> dict:
        return await self._post("/qc/batch-submit", {"results": [m.model_dump() for m in measurements]})

    async def qc_list(self, page: int = 1, limit: int = 50, **filters: Any) -> dict:
        return await self._get("/qc", query={"page": page, "limit": limit, **filters})

    # ── AI ────────────────────────────────────────────────────────────────────

    async def ai_suggest(self, request: SuggestRequest) -> dict:
        return await self._post("/ai/suggest", request.model_dump())

    async def ai_reject_suggestion(self, suggestion_id: int, reason: str | None = None) -> dict:
        return await self._post(f"/ai/suggest/{suggestion_id}/reject", RejectRequest(reason=reason).model_dump())

    async def ai_chat(self, message: str, context: str | None = None) -> dict:
        return await self._post("/ai/chat", ChatRequest(message=message, context=context).model_dump())

    async def ai_log_interaction(self, interaction: InteractionIn) -> InteractionOut:
        data = await self._post("/api/ai/interactions", interaction.model_dump())
        return InteractionOut(**data)

    async def ai_log_feedback(self, feedback: FeedbackIn) -> dict:
        return await self._post("/api/ai/feedback", feedback.model_dump())

    async def ai_log_unresolved(self, unresolved: UnresolvedIn) -> dict:
        return await self._post("/api/ai/unresolved", unresolved.model_dump())

    # ── Stats & Dashboard ─────────────────────────────────────────────────────

    async def dashboard_main(self) -> dict:
        return await self._get("/dashboard")

    async def dashboard_lab(self, lab_id: int) -> dict:
        return await self._get(f"/dashboard/lab/{lab_id}")

    async def stats_overview(self) -> dict:
        return await self._get("/stats")

    # ── Compliance ────────────────────────────────────────────────────────────

    async def compliance_check(self) -> dict:
        return await self._get("/compliance")

    async def compliance_report(self) -> dict:
        return await self._get("/compliance/report")

    # ── Governance ────────────────────────────────────────────────────────────

    async def governance_create_node(self, node: NodeCreate) -> dict:
        return await self._post("/governance/nodes", node.model_dump())

    async def governance_list_nodes(self, page: int = 1, limit: int = 50) -> dict:
        return await self._get("/governance/nodes", query={"page": page, "limit": limit})

    async def governance_create_delegation(self, delegation: DelegationCreate) -> dict:
        return await self._post("/governance/delegations", delegation.model_dump())

    async def governance_appoint_acting(self, appointment: ActingAppoint) -> dict:
        return await self._post("/governance/acting-appointments", appointment.model_dump())

    async def governance_create_worker(self, worker: WorkerCreate) -> dict:
        return await self._post("/governance/workers", worker.model_dump())

    async def governance_register_lab(self, lab: LabRegister) -> dict:
        return await self._post("/governance/laboratories", lab.model_dump())

    # ── LIMS ──────────────────────────────────────────────────────────────────

    async def lims_register_specimen(self, specimen: SpecimenRegisterRequest) -> dict:
        return await self._post("/lims/specimens", specimen.model_dump())

    async def lims_transition_specimen(self, specimen_id: int, transition: SpecimenTransitionRequest) -> dict:
        return await self._post(f"/lims/specimens/{specimen_id}/transition", transition.model_dump())

    async def lims_create_order(self, order: OrderCreateRequest) -> dict:
        return await self._post("/lims/orders", order.model_dump())

    async def lims_create_result(self, result: ResultCreateRequest) -> dict:
        return await self._post("/lims/results", result.model_dump())

    async def lims_validate_result(self, result_id: int, validation: ResultValidateRequest) -> dict:
        return await self._post(f"/lims/results/{result_id}/validate", validation.model_dump())

    async def lims_qc_run(self, qc: IQCRunRequest) -> dict:
        return await self._post("/lims/qc/runs", qc.model_dump())

    async def lims_register_instrument(self, instrument: InstrumentCreateRequest) -> dict:
        return await self._post("/lims/instruments", instrument.model_dump())

    async def lims_record_maintenance(self, instrument_id: int, maintenance: MaintenanceRecordRequest) -> dict:
        return await self._post(f"/lims/instruments/{instrument_id}/maintenance", maintenance.model_dump())

    async def lims_record_calibration(self, instrument_id: int, calibration: CalibrationRecordRequest) -> dict:
        return await self._post(f"/lims/instruments/{instrument_id}/calibrations", calibration.model_dump())

    async def lims_update_inventory(self, inventory: InventoryRequest) -> dict:
        return await self._post("/lims/inventory", inventory.model_dump())

    async def lims_generate_report(self, report: ReportGenerateRequest) -> dict:
        return await self._post("/lims/reports", report.model_dump())

    async def lims_device_message(self, message: DeviceMessageRequest) -> dict:
        return await self._post("/lims/devices/message", message.model_dump())

    # ── FHIR ──────────────────────────────────────────────────────────────────

    async def fhir_search(self, resource_type: str, **params: Any) -> dict:
        return await self._get(f"/fhir/{resource_type}", query=params)

    async def fhir_read(self, resource_type: str, resource_id: str) -> dict:
        return await self._get(f"/fhir/{resource_type}/{resource_id}")

    async def fhir_create(self, resource_type: str, resource: dict) -> dict:
        return await self._post(f"/fhir/{resource_type}", resource)

    async def fhir_update(self, resource_type: str, resource_id: str, resource: dict) -> dict:
        return await self._put(f"/fhir/{resource_type}/{resource_id}", resource)

    async def fhir_delete(self, resource_type: str, resource_id: str) -> None:
        await self._delete(f"/fhir/{resource_type}/{resource_id}")

    async def fhir_capabilities(self) -> dict:
        return await self._get("/fhir/metadata")

    # ── Tiers / Subscription ──────────────────────────────────────────────────

    async def request_upgrade(self, request: UpgradeRequestBody) -> dict:
        return await self._post("/tiers/upgrade", request.model_dump())

    async def signal_upgrade_demand(self, signal: DemandSignalBody) -> dict:
        return await self._post("/tiers/upgrade-demand", signal.model_dump())

    # ── QR ────────────────────────────────────────────────────────────────────

    async def generate_qr(self, data: dict) -> dict:
        return await self._post("/qr/generate", data)

    async def verify_qr(self, qr_data: dict) -> dict:
        return await self._post("/qr/verify", qr_data)

    # ── ID Scan ───────────────────────────────────────────────────────────────

    async def scan_id(self, image_bytes: bytes, filename: str) -> dict:
        url = f"{self.base_url}/id-scan"
        headers = self._build_headers()
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, files={"file": (filename, image_bytes)})
            if not resp.is_success:
                raise map_status_code(resp.status_code, self._try_decode(resp))
            return resp.json()

    # ── Metrics ───────────────────────────────────────────────────────────────

    async def metrics_prometheus(self) -> str:
        return await self._get("/metrics/prom")

    # ── Setup ─────────────────────────────────────────────────────────────────

    async def setup_init(
        self,
        admin_email: str,
        admin_password: str,
        lab_name: str,
    ) -> dict:
        return await self._post(
            "/setup/init",
            {"admin_email": admin_email, "admin_password": admin_password, "lab_name": lab_name},
        )

    # ── EHR ───────────────────────────────────────────────────────────────────

    async def ehr_export(self, patient_id: int, format: str = "json") -> Any:
        return await self._get(f"/ehr/export/{patient_id}", query={"format": format})

    # ── Insurance ─────────────────────────────────────────────────────────────

    async def insurance_verify(self, policy_number: str) -> dict:
        return await self._get(f"/insurance/verify/{policy_number}")

    # ── Mobile ────────────────────────────────────────────────────────────────

    async def mobile_register(self, device_token: str, platform: str, **kwargs: Any) -> dict:
        return await self.register_device(device_token, platform, **kwargs)
