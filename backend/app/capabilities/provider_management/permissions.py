from __future__ import annotations

from enum import Enum


class Provider_managementPermission(Enum):
    READ = "provider_management:provider.read"
    CREATE = "provider_management:provider.create"
    UPDATE = "provider_management:provider.update"
    ADMIN = "provider_management:provider.admin"

    def describe(self) -> str:
        descriptions = {        "provider_management:provider.read": "Provider.Read",
                "provider_management:provider.create": "Provider.Create",
                "provider_management:provider.update": "Provider.Update",
                "provider_management:provider.admin": "Provider.Admin"}
        return descriptions.get(self, self.value)
