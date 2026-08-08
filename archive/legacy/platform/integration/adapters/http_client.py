from dataclasses import dataclass, field
from typing import Any


@dataclass
class HTTPConfig:
    base_url: str = ""
    timeout: float = 30.0
    max_retries: int = 3
    headers: dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True


class HttpClientAdapter:
    def __init__(self, config: HTTPConfig | None = None):
        self._config = config or HTTPConfig()
        self._session = None

    async def connect(self) -> None:
        import httpx
        self._session = httpx.AsyncClient(
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            headers=self._config.headers,
            verify=self._config.verify_ssl,
        )

    async def disconnect(self) -> None:
        if self._session:
            await self._session.aclose()
            self._session = None

    async def get(self, path: str, **kwargs) -> Any:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Any:
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Any:
        return await self._request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Any:
        return await self._request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Any:
        return await self._request("DELETE", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        import httpx
        if self._session is None:
            raise RuntimeError("HTTP client not connected")

        last_error = None
        for attempt in range(self._config.max_retries):
            try:
                response = await self._session.request(method, path, **kwargs)
                return response
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < self._config.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(1 * (2 ** attempt))
        raise last_error  # type: ignore

    def is_connected(self) -> bool:
        return self._session is not None
