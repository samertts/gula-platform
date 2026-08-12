from __future__ import annotations

from .base import BaseConnector


class ConnectorRegistry:
    _connectors: dict[str, BaseConnector] = {}

    @classmethod
    def register(cls, name: str, connector: BaseConnector) -> None:
        cls._connectors[name] = connector

    @classmethod
    def get(cls, name: str) -> BaseConnector | None:
        return cls._connectors.get(name)

    @classmethod
    def unregister(cls, name: str) -> None:
        cls._connectors.pop(name, None)

    @classmethod
    def list(cls) -> list[dict]:
        return [
            {
                "name": name,
                "status": conn.get_status().value,
                "protocol": conn._config.protocol.value,
                "direction": conn._config.direction.value,
                "metrics": conn.get_metrics(),
            }
            for name, conn in cls._connectors.items()
        ]

    @classmethod
    def health_all(cls) -> dict[str, bool]:
        import asyncio

        async def _check_all() -> dict[str, bool]:
            results: dict[str, bool] = {}
            for name, conn in cls._connectors.items():
                try:
                    results[name] = await conn.health_check()
                except Exception:
                    results[name] = False
            return results

        return asyncio.run(_check_all())

    @classmethod
    def find_by_protocol(cls, protocol: str) -> list[BaseConnector]:
        return [c for c in cls._connectors.values() if c._config.protocol.value == protocol]

    @classmethod
    def find_by_direction(cls, direction: str) -> list[BaseConnector]:
        return [c for c in cls._connectors.values() if c._config.direction.value == direction]

    @classmethod
    def clear(cls) -> None:
        cls._connectors.clear()

    @classmethod
    def count(cls) -> int:
        return len(cls._connectors)
