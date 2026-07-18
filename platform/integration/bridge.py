from dataclasses import dataclass, field
from typing import Any


@dataclass
class BridgeConfig:
    database_url: str = ""
    redis_url: str = ""
    enable_monolith: bool = True
    enable_database: bool = True
    enable_redis: bool = True
    enable_http: bool = True


class IntegrationBridge:
    def __init__(self, config: BridgeConfig | None = None):
        self._config = config or BridgeConfig()
        self._db: Any = None
        self._redis: Any = None
        self._http: Any = None
        self._monolith: Any = None

    async def bootstrap(self) -> None:
        if self._config.enable_database and self._config.database_url:
            from platform.integration.adapters.database import DatabaseAdapter, DatabaseConfig
            db_config = DatabaseConfig(url=self._config.database_url)
            self._db = DatabaseAdapter(db_config)
            await self._db.connect()

        if self._config.enable_redis and self._config.redis_url:
            from platform.integration.adapters.redis_adapter import RedisAdapter, RedisConfig
            redis_config = RedisConfig(url=self._config.redis_url)
            self._redis = RedisAdapter(redis_config)
            await self._redis.connect()

        if self._config.enable_http:
            from platform.integration.adapters.http_client import HttpClientAdapter, HTTPConfig
            self._http = HttpClientAdapter()
            await self._http.connect()

        if self._config.enable_monolith:
            from platform.integration.adapters.monolith import MonolithAdapter
            self._monolith = MonolithAdapter()

    async def shutdown(self) -> None:
        if self._db:
            await self._db.disconnect()
        if self._redis:
            await self._redis.disconnect()
        if self._http:
            await self._http.disconnect()

    @property
    def db(self) -> Any:
        return self._db

    @property
    def redis(self) -> Any:
        return self._redis

    @property
    def http(self) -> Any:
        return self._http

    @property
    def monolith(self) -> Any:
        return self._monolith

    def is_ready(self) -> bool:
        return all([
            not self._config.enable_database or (self._db and self._db.is_connected()),
            not self._config.enable_redis or (self._redis and self._redis.is_connected()),
        ])
