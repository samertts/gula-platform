"""GULA Communication Provider Layer (PROGRAM-COMM-002).

Provider plugins plug into the provider-independent Communication Core
(``shared.communication``) through the plugin system. The Core is never
modified; adding a provider is always a new plugin.

Providers shipped: Resend (email), Telegram, Discord, Slack, Microsoft
Teams, generic webhooks, in-app notifications, plus the push and SMS
channel abstractions (no vendor shipped — third parties implement the
contract in their own plugin).
"""

from __future__ import annotations

from .background import BackgroundDelivery, BackgroundDispatcher
from .base import (
    BaseChannelProvider,
    ProviderMetrics,
    ProviderSettings,
    Redactor,
    TokenBucket,
)
from .plugins import (
    BUILTIN_PLUGIN_CLASSES,
    load_provider_plugins,
    provider_enabled,
    register_builtin_plugins,
)
from .plugins.discord import DiscordPlugin, DiscordProvider
from .plugins.inapp import InAppPlugin, InAppProvider, InAppRecord, InMemoryInAppSink
from .plugins.push import NoopPushPlugin, NoopPushProvider, PushProvider
from .plugins.resend import ResendPlugin, ResendProvider
from .plugins.slack import SlackPlugin, SlackProvider
from .plugins.sms import NoopSmsPlugin, NoopSmsProvider, SmsProvider
from .plugins.teams import TeamsPlugin, TeamsProvider
from .plugins.telegram import TelegramPlugin, TelegramProvider
from .plugins.webhook import WebhookPlugin, WebhookProvider
from .secrets import SecretResolver, SecretSpec, token_secret_name, webhook_secret_name
from .transport import (
    CircuitOpenError,
    HttpTransport,
    TransportResponse,
    TransportSettings,
)

__all__ = [
    "BUILTIN_PLUGIN_CLASSES",
    "BackgroundDelivery",
    "BackgroundDispatcher",
    "BaseChannelProvider",
    "CircuitOpenError",
    "DiscordPlugin",
    "DiscordProvider",
    "HttpTransport",
    "InAppPlugin",
    "InAppProvider",
    "InAppRecord",
    "InMemoryInAppSink",
    "NoopPushPlugin",
    "NoopPushProvider",
    "NoopSmsPlugin",
    "NoopSmsProvider",
    "ProviderMetrics",
    "ProviderSettings",
    "PushProvider",
    "Redactor",
    "ResendPlugin",
    "ResendProvider",
    "SecretResolver",
    "SecretSpec",
    "SlackPlugin",
    "SlackProvider",
    "SmsProvider",
    "TeamsPlugin",
    "TeamsProvider",
    "TelegramPlugin",
    "TelegramProvider",
    "TokenBucket",
    "TransportResponse",
    "TransportSettings",
    "WebhookPlugin",
    "WebhookProvider",
    "load_provider_plugins",
    "provider_enabled",
    "register_builtin_plugins",
    "token_secret_name",
    "webhook_secret_name",
]
