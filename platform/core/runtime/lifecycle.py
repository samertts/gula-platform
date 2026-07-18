from enum import Enum


class ApplicationLifecycle:
    def __init__(self):
        self._listeners: dict[str, list[callable]] = {}

    def on(self, event: str, handler: callable) -> None:
        self._listeners.setdefault(event, []).append(handler)

    def off(self, event: str, handler: callable) -> None:
        handlers = self._listeners.get(event, [])
        if handler in handlers:
            handlers.remove(handler)

    async def emit(self, event: str, *args, **kwargs) -> None:
        for handler in self._listeners.get(event, []):
            try:
                result = handler(*args, **kwargs)
                if hasattr(result, "__await__"):
                    await result
            except Exception:
                pass

    def clear(self) -> None:
        self._listeners.clear()
