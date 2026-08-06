from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("nhdw.api")


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 0, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class AuthError(ApiError):
    pass


class NetworkError(ApiError):
    pass


class ValidationError(ApiError):
    pass


class NotFoundError(ApiError):
    pass


class ApiClient:
    _instance: ApiClient | None = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_url: str = "", timeout: int = 30):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token: str | None = None
        self.refresh_token: str | None = None
        self._refresh_url = f"{self.base_url}/auth/refresh"

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "PUT", "DELETE"],
        )
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def set_base_url(self, url: str):
        self.base_url = url.rstrip("/")
        self._refresh_url = f"{self.base_url}/auth/refresh"

    @property
    def is_authenticated(self) -> bool:
        return self.token is not None

    def login(self, username: str, password: str) -> dict[str, Any]:
        try:
            resp = self._session.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token") or data.get("token")
                self.refresh_token = data.get("refresh_token", "")
                return data
            if resp.status_code == 401:
                raise AuthError("Invalid credentials", status_code=401)
            if resp.status_code == 422:
                raise ValidationError("Validation error", status_code=422, response=resp.json())
            self._handle_error(resp)
        except requests.ConnectionError:
            raise NetworkError("Cannot connect to server")
        except requests.Timeout:
            raise NetworkError("Request timed out")
        return {}

    def logout(self):
        self.token = None
        self.refresh_token = None

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _refresh_token(self) -> bool:
        if not self.refresh_token:
            return False
        try:
            resp = self._session.post(
                self._refresh_url,
                json={"refresh_token": self.refresh_token},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token") or data.get("token")
                return True
        except Exception:
            pass
        return False

    def _handle_error(self, resp: requests.Response):
        status = resp.status_code
        try:
            detail = resp.json()
        except (json.JSONDecodeError, ValueError):
            detail = {"detail": resp.text}

        if status == 401:
            raise AuthError(detail.get("detail", "Unauthorized"), status, detail)
        if status == 403:
            raise AuthError(detail.get("detail", "Forbidden"), status, detail)
        if status == 404:
            raise NotFoundError(detail.get("detail", "Not found"), status, detail)
        if status == 422:
            raise ValidationError(detail.get("detail", "Validation error"), status, detail)
        if status >= 500:
            raise ApiError(detail.get("detail", "Server error"), status, detail)
        raise ApiError(detail.get("detail", f"HTTP {status}"), status, detail)

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        kwargs.setdefault("timeout", self.timeout)
        kwargs["headers"] = {**self._get_headers(), **kwargs.pop("headers", {})}

        for attempt in range(2):
            try:
                resp = self._session.request(method, url, **kwargs)
                if resp.status_code == 401 and attempt == 0:
                    if self._refresh_token():
                        kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
                        continue
                    raise AuthError("Session expired", status_code=401)
                if resp.status_code == 204:
                    return {}
                if resp.status_code >= 400:
                    self._handle_error(resp)
                return resp.json()
            except requests.ConnectionError:
                if attempt == 0:
                    time.sleep(1)
                    continue
                raise NetworkError("Connection failed")
        return {}

    def get(self, endpoint: str, params: dict | None = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict | None = None) -> Any:
        return self._request("POST", endpoint, json=data or {})

    def put(self, endpoint: str, data: dict | None = None) -> Any:
        return self._request("PUT", endpoint, json=data or {})

    def delete(self, endpoint: str) -> Any:
        return self._request("DELETE", endpoint)

    def upload_file(self, endpoint: str, filepath: str | Path, field_name: str = "file") -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        with open(filepath, "rb") as f:
            resp = self._session.post(
                url,
                files={field_name: f},
                headers=headers,
                timeout=self.timeout * 2,
            )
        if resp.status_code >= 400:
            self._handle_error(resp)
        return resp.json()

    def download_file(self, url: str, dest_path: str | Path):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = self._session.get(url, headers=headers, timeout=self.timeout * 2, stream=True)
        if resp.status_code >= 400:
            self._handle_error(resp)
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
