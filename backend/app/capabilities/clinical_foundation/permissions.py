from __future__ import annotations

from enum import Enum


class Clinical_foundationPermission(Enum):
    CLINICAL.READ = "clinical_foundation:clinical.read"
    CLINICAL.WRITE = "clinical_foundation:clinical.write"
    CLINICAL.ADMIN = "clinical_foundation:clinical.admin"

    def describe(self) -> str:
        descriptions = {        "clinical_foundation:clinical.read": "Clinical.Read",
                "clinical_foundation:clinical.write": "Clinical.Write",
                "clinical_foundation:clinical.admin": "Clinical.Admin"}
        return descriptions.get(self, self.value)
