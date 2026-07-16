from __future__ import annotations

import logging
from typing import Any, TypeVar

from app.kernel.exceptions import ServiceNotFoundError
from app.kernel.types import ServiceDescriptor, ServiceLifecycle

logger = logging.getLogger("gula.kernel.di")

T = TypeVar("T")


class DIContainer:
    def __init__(self):
        self._descriptors: dict[str, ServiceDescriptor] = {}
        self._singletons: dict[str, Any] = {}
        self._scoped: dict[str, dict[str, Any]] = {}

    def register(self, descriptor: ServiceDescriptor) -> None:
        self._descriptors[descriptor.name] = descriptor

    def resolve(self, name: str, scope_id: str | None = None) -> Any:
        descriptor = self._descriptors.get(name)
        if not descriptor:
            raise ServiceNotFoundError(name)

        if descriptor.lifecycle == ServiceLifecycle.SINGLETON:
            if name not in self._singletons:
                self._singletons[name] = self._build(descriptor)
            return self._singletons[name]

        if descriptor.lifecycle == ServiceLifecycle.SCOPED:
            if scope_id is None:
                scope_id = "default"
            if scope_id not in self._scoped:
                self._scoped[scope_id] = {}
            if name not in self._scoped[scope_id]:
                self._scoped[scope_id][name] = self._build(descriptor)
            return self._scoped[scope_id][name]

        return self._build(descriptor)

    def _build(self, descriptor: ServiceDescriptor) -> Any:
        resolved_deps = []
        for dep_name in descriptor.dependencies:
            dep = self.resolve(dep_name)
            resolved_deps.append(dep)
        return descriptor.implementation(*resolved_deps)

    def clear_scope(self, scope_id: str) -> None:
        self._scoped.pop(scope_id, None)
