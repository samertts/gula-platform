from __future__ import annotations

from enum import Enum


class Encounter_managementPermission(Enum):
    READ = "encounter_management:encounter.read"
    CREATE = "encounter_management:encounter.create"
    UPDATE = "encounter_management:encounter.update"
    ADMIN = "encounter_management:encounter.admin"

    def describe(self) -> str:
        descriptions = {        "encounter_management:encounter.read": "Encounter.Read",
                "encounter_management:encounter.create": "Encounter.Create",
                "encounter_management:encounter.update": "Encounter.Update",
                "encounter_management:encounter.admin": "Encounter.Admin"}
        return descriptions.get(self, self.value)
