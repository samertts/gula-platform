from dataclasses import dataclass
from typing import Any


@dataclass
class RedisConfig:
    url: str = "redis://localhost:6379/0"
    password: str | None = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    max_connections: int = 20
    decode_responses: bool = True


class RedisAdapter:
    def __init__(self, config: RedisConfig | None = None):
        self._config = config or RedisConfig()
        self._client = None

    async def connect(self) -> None:
        import redis.asyncio as aioredis
        self._client = aioredis.from_url(
            self._config.url,
            password=self._config.password,
            socket_timeout=self._config.socket_timeout,
            socket_connect_timeout=self._config.socket_connect_timeout,
            retry_on_timeout=self._config.retry_on_timeout,
            max_connections=self._config.max_connections,
            decode_responses=self._config.decode_responses,
        )

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, key: str) -> str | None:
        if self._client is None:
            return None
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        if self._client is None:
            return False
        return await self._client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> bool:
        if self._client is None:
            return False
        return bool(await self._client.delete(key))

    async def exists(self, key: str) -> bool:
        if self._client is None:
            return False
        return bool(await self._client.exists(key))

    async def expire(self, key: str, ttl: int) -> bool:
        if self._client is None:
            return False
        return await self._client.expire(key, ttl)

    async def publish(self, channel: str, message: str) -> int:
        if self._client is None:
            return 0
        return await self._client.publish(channel, message)

    async def subscribe(self, channel: str) -> Any:
        if self._client is None:
            return None
        pubsub = self._client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def health(self) -> dict[str, Any]:
        if self._client is None:
            return {"status": "disconnected"}
        try:
            await self._client.ping()
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def is_connected(self) -> bool:
        return self._client is not None

    @property
    def client(self) -> Any:
        return self._client
