from __future__ import annotations

import json
import sys
import time
from typing import Any

import httpx
from rich import print as rprint

from .config import Config

_RETRYABLE = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3


class GulaClient:
    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config()
        self._base_url = self._config.base_url

    @property
    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        token = self._config.token
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def _request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        last_exc: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = httpx.request(
                    method=method,
                    url=url,
                    headers=self._headers,
                    params=query,
                    json=body,
                    timeout=30.0,
                )

                if attempt > 1:
                    print(f"  retry attempt {attempt}/{_MAX_RETRIES}", file=sys.stderr)

                if resp.is_success:
                    if resp.status_code == 204:
                        return None
                    ct = resp.headers.get("content-type", "")
                    if "application/json" in ct:
                        return resp.json()
                    return resp.text

                if resp.status_code in _RETRYABLE and attempt < _MAX_RETRIES:
                    backoff = 2 ** attempt
                    print(
                        f"  HTTP {resp.status_code}, retrying in {backoff}s (attempt {attempt}/{_MAX_RETRIES})",
                        file=sys.stderr,
                    )
                    time.sleep(backoff)
                    continue

                self._handle_error(resp)

            except httpx.TimeoutException as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    backoff = 2 ** attempt
                    print(f"  timeout, retrying in {backoff}s", file=sys.stderr)
                    time.sleep(backoff)
                    continue
            except httpx.TransportError as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    backoff = 2 ** attempt
                    print(f"  transport error, retrying in {backoff}s", file=sys.stderr)
                    time.sleep(backoff)
                    continue

        if last_exc:
            raise SystemExit(f"error: {last_exc}")
        return None

    def _handle_error(self, resp: httpx.Response) -> None:
        detail = ""
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        msg = f"error [{resp.status_code}]: {detail}"
        if resp.status_code == 401:
            msg = "authentication failed — run 'gula auth login'"
        elif resp.status_code == 403:
            msg = "permission denied"
        elif resp.status_code == 404:
            msg = "not found"
        rprint(f"[red]{msg}[/red]")
        raise SystemExit(1)

    def _get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, query=query)

    def _post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, body=body)

    def _put(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return self._request("PUT", path, body=body)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def login(self, email: str, password: str) -> dict:
        return self._post("/login", {"email": email, "password": password})

    def refresh_token(self) -> dict:
        return self._post("/auth/refresh", {"refresh_token": self._config.refresh_token})

    def list_patients(self, page: int = 1, limit: int = 50, search: str | None = None) -> dict:
        query: dict[str, Any] = {"page": page, "limit": limit}
        if search:
            query["search"] = search
        return self._get("/patients", query=query)

    def get_patient(self, patient_id: int) -> dict:
        return self._get(f"/patients/{patient_id}")

    def create_patient(self, data: dict) -> dict:
        return self._post("/patients", data)

    def list_orders(self, page: int = 1, limit: int = 50) -> dict:
        return self._get("/orders", {"page": page, "limit": limit})

    def get_order(self, order_id: int) -> dict:
        return self._get(f"/orders/{order_id}")

    def create_order(self, data: dict) -> dict:
        return self._post("/orders", data)

    def list_results(self, page: int = 1, limit: int = 50) -> dict:
        return self._get("/results", {"page": page, "limit": limit})

    def get_result(self, result_id: int) -> dict:
        return self._get(f"/results/{result_id}")

    def list_labs(self, page: int = 1, limit: int = 50) -> dict:
        return self._get("/labs", {"page": page, "limit": limit})

    def get_lab(self, lab_id: int) -> dict:
        return self._get(f"/labs/{lab_id}")

    def list_samples(self, page: int = 1, limit: int = 50) -> dict:
        return self._get("/samples", {"page": page, "limit": limit})

    def get_sample(self, sample_id: int) -> dict:
        return self._get(f"/samples/{sample_id}")

    def grant_consent(self, data: dict) -> dict:
        return self._post("/consent/grant", data)

    def check_consent(self, gpid: str, scope: str) -> dict:
        return self._get("/consent/check", {"gpid": gpid, "scope": scope})

    def list_claims(self, page: int = 1, limit: int = 50) -> dict:
        return self._get("/claims", {"page": page, "limit": limit})

    def create_claim(self, data: dict) -> dict:
        return self._post("/claims", data)

    def edge_list_devices(self, page: int = 1, limit: int = 50) -> dict:
        return self._get("/edge/devices", {"page": page, "limit": limit})

    def edge_list_tasks(self, page: int = 1, limit: int = 50) -> dict:
        return self._get("/edge/tasks", {"page": page, "limit": limit})

    def fhir_get_patient(self, patient_id: str) -> dict:
        return self._get(f"/fhir/Patient/{patient_id}")

    def fhir_get_observation(self, observation_id: str) -> dict:
        return self._get(f"/fhir/Observation/{observation_id}")

    def mpi_resolve(self, data: dict) -> dict:
        return self._post("/mpi/resolve", data)

    def stats_dashboard(self) -> dict:
        return self._get("/stats/dashboard")

    def health(self) -> dict:
        return self._get("/health")

    def test_types(self) -> list:
        return self._get("/test-types")

    def dashboard(self) -> dict:
        return self._get("/dashboard")
