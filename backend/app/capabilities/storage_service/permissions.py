from __future__ import annotations

from enum import Enum


class Storage_servicePermission(Enum):
    STORAGE.READ = "storage_service:storage.read"
    STORAGE.WRITE = "storage_service:storage.write"
    STORAGE.DELETE = "storage_service:storage.delete"
    STORAGE.ADMIN = "storage_service:storage.admin"

    def describe(self) -> str:
        descriptions = {        "storage_service:storage.read": "Storage.Read",
                "storage_service:storage.write": "Storage.Write",
                "storage_service:storage.delete": "Storage.Delete",
                "storage_service:storage.admin": "Storage.Admin"}
        return descriptions.get(self, self.value)
