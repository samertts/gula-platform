from __future__ import annotations

from enum import StrEnum


class CommunicationMode(StrEnum):
    LOCAL_ONLY = "local_only"
    HYBRID = "hybrid"
    CLOUD_ONLY = "cloud_only"
