"""
shared.di_container — Enterprise-grade dependency injection container.

Extracted from Platform-Core and adapted for GULA's shared library.
Provides singleton, scoped, and transient lifetimes with auto-wiring,
circular dependency detection, and thread safety.
"""

from .engine import ServiceContainer, ServiceScope
from .exceptions import (
    ContainerError,
    ServiceAlreadyRegisteredError,
    ServiceNotRegisteredError,
)
from .lifetime import Lifetime
from .service_descriptor import ServiceDescriptor

__all__ = [
    "ContainerError",
    "Lifetime",
    "ServiceAlreadyRegisteredError",
    "ServiceContainer",
    "ServiceDescriptor",
    "ServiceNotRegisteredError",
    "ServiceScope",
]
