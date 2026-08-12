import functools
import logging
from typing import Any

from platform.core.modules.module import Module, ModuleManifest


_registered_modules: dict[str, type[Module]] = {}


def module(
    name: str,
    version: str = "1.0.0",
    description: str = "",
    dependencies: list[str] | None = None,
    events_published: list[str] | None = None,
    events_subscribed: list[str] | None = None,
    commands_handled: list[str] | None = None,
    queries_handled: list[str] | None = None,
):
    def decorator(cls: type) -> type:
        manifest = ModuleManifest(
            name=name,
            version=version,
            description=description,
            dependencies=dependencies or [],
            events_published=events_published or [],
            events_subscribed=events_subscribed or [],
            commands_handled=commands_handled or [],
            queries_handled=queries_handled or [],
        )

        original_init = cls.__init__

        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            Module.__init__(self, manifest)
            if original_init is not object.__init__:
                original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        _registered_modules[name] = cls
        logging.getLogger("gula.modules").debug("Module registered via decorator: %s v%s", name, version)
        return cls

    return decorator


def get_registered_modules() -> dict[str, type[Module]]:
    return dict(_registered_modules)


def get_module_class(name: str) -> type[Module] | None:
    return _registered_modules.get(name)


def clear_registered_modules() -> None:
    _registered_modules.clear()
