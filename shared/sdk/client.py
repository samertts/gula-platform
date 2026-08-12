from __future__ import annotations

from typing import Any

import httpx

from shared.sdk.exceptions import AuthenticationError, NotFoundError, ValidationError


class GulaClient:
    def __init__(self, base_url: str = "http://localhost:8080", api_key: str | None = None, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url, timeout=timeout,
            headers=self._build_headers(api_key),
        )

    def _build_headers(self, api_key: str | None) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def request(self, method: str, path: str, params: dict[str, Any] | None = None, data: dict[str, Any] | None = None) -> Any:
        url = f"/api/v1{path}" if not path.startswith("/") else path
        response = self._client.request(method, url, params=params, json=data)
        if response.status_code >= 400:
            detail = response.json().get("detail", str(response.content))
            if response.status_code == 401:
                raise AuthenticationError(detail)
            if response.status_code == 404:
                raise NotFoundError(detail)
            if response.status_code == 422:
                raise ValidationError(detail)
            response.raise_for_status()
        return response.json()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, data: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, data=data)

    def put(self, path: str, data: dict[str, Any] | None = None) -> Any:
        return self.request("PUT", path, data=data)

    def patch(self, path: str, data: dict[str, Any] | None = None) -> Any:
        return self.request("PATCH", path, data=data)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    def health(self) -> dict[str, Any]:
        return self.get("/health")

    def create_patient(self, data: dict[str, Any]) -> Any:
        return self.post("/patients", data)

    def get_patient(self, patient_id: int) -> Any:
        return self.get(f"/patients/{patient_id}")

    def list_patients(self, lab_id: int | None = None, skip: int = 0, limit: int = 100) -> Any:
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if lab_id is not None:
            params["lab_id"] = lab_id
        return self.get("/patients", params=params)

    def create_order(self, data: dict[str, Any]) -> Any:
        return self.post("/orders", data)

    def get_order(self, order_id: int) -> Any:
        return self.get(f"/orders/{order_id}")

    def list_orders(self, lab_id: int | None = None, patient_id: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if lab_id is not None:
            params["lab_id"] = lab_id
        if patient_id is not None:
            params["patient_id"] = patient_id
        return self.get("/orders", params=params)

    def create_result(self, data: dict[str, Any]) -> Any:
        return self.post("/results", data)

    def get_result(self, result_id: int) -> Any:
        return self.get(f"/results/{result_id}")

    def list_results(self, order_id: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if order_id is not None:
            params["order_id"] = order_id
        return self.get("/results", params=params)

    def create_sample(self, data: dict[str, Any]) -> Any:
        return self.post("/samples", data)

    def get_sample(self, sample_id: int) -> Any:
        return self.get(f"/samples/{sample_id}")

    def get_lab(self, lab_id: int) -> Any:
        return self.get(f"/labs/{lab_id}")

    def close(self) -> None:
        self._client.close()


__all__ = ["GulaClient"]
