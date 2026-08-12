from enum import Enum
from abc import ABC, abstractmethod


class LifecycleEvent(Enum):
    BOOTING = "booting"
    CONFIGURED = "configured"
    REGISTERED = "registered"
    STARTED = "started"
    READY = "ready"
    PAUSING = "pausing"
    PAUSED = "paused"
    RESUMING = "resuming"
    RESUMED = "resumed"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    HEALTH_DEGRADED = "health_degraded"
    HEALTH_CRITICAL = "health_critical"
    HEALTH_RESTORED = "health_restored"


class LifecycleListener(ABC):
    @abstractmethod
    def on_lifecycle_event(self, event: LifecycleEvent) -> None:
        ...
