"""Bridge to shared MessageBroker."""
import warnings
warnings.warn(
    "services/shared/messaging.py is deprecated. Import from 'shared.messaging' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from shared.messaging import MessageBroker

__all__ = [
    "MessageBroker",
]
