from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.kernel import Kernel

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "kernel_request_id", default=""
)
tenant_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("kernel_tenant_id", default="")
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("kernel_user_id", default="")
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "kernel_correlation_id", default=""
)


class ApplicationContext:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self._attributes: dict[str, object] = {}

    def set_request_id(self, request_id: str) -> None:
        request_id_var.set(request_id)

    def get_request_id(self) -> str:
        return request_id_var.get()

    def set_tenant_id(self, tenant_id: str) -> None:
        tenant_id_var.set(tenant_id)

    def get_tenant_id(self) -> str:
        return tenant_id_var.get()

    def set_correlation_id(self, correlation_id: str) -> None:
        correlation_id_var.set(correlation_id)

    def get_correlation_id(self) -> str:
        return correlation_id_var.get()

    def set(self, key: str, value: object) -> None:
        self._attributes[key] = value

    def get(self, key: str, default: object = None) -> object | None:
        return self._attributes.get(key, default)

    def clear(self) -> None:
        self._attributes.clear()
