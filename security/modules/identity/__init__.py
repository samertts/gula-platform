GSF-001: Identity Module — Multi-tenant identity provider.

Provides identity management for the GULA platform including national ID (NIN)
integration, multi-tenant user directories, identity federation, and
identity lifecycle management.

Exports:
    IdentityProvider: Core identity provider service
    IdentityDirectory: Directory-backed identity store
    NationalIdValidator: Iraqi National Identification Number (NIN) validator
    TenantResolver: Multi-tenant identity resolution
    IdentityEvent: Identity lifecycle event model
"""

from security.modules.identity.provider import IdentityProvider
from security.modules.identity.directory import IdentityDirectory
from security.modules.identity.validators import NationalIdValidator
from security.modules.identity.tenant import TenantResolver
from security.modules.identity.events import IdentityEvent

__all__ = [
    "IdentityProvider",
    "IdentityDirectory",
    "NationalIdValidator",
    "TenantResolver",
    "IdentityEvent",
]
