"""GULA Communication Platform Core — provider-independent communication
infrastructure shared by every GULA application.

This package is the ONLY sanctioned entry point for communication. It
contains no provider implementation and imports nothing outside the standard
library — provider plugins (PROGRAM-COMM-002) plug in through the registry,
never into the Core.
"""

from __future__ import annotations

import logging

from .audit import (
    AuditAction,
    AuditEvent,
    AuditSink,
    CompositeAuditSink,
    LoggingAuditSink,
    NullAuditSink,
)
from .center import CommunicationCenter
from .config import CommunicationConfig
from .events import CommunicationEventHandler, EventBridge, EventPolicyRegistry
from .model import (
    Attachment,
    ChannelAttempt,
    ContentFormat,
    DeliveryReceipt,
    OutboundMessage,
    Priority,
    ProviderDeliveryResult,
    Recipient,
    new_delivery_id,
)
from .plugins import (
    ENTRY_POINT_GROUP,
    PluginManager,
    PluginMetadata,
    PluginState,
    ProviderPlugin,
)
from .policy import (
    MANDATORY_PRIORITY,
    Policy,
    PolicyDecision,
    PolicyEngine,
    PreferenceStore,
    RecipientPreferences,
)
from .providers import (
    AlertCapability,
    BulkCapability,
    ChannelCapability,
    ChannelProvider,
    MediaCapability,
    ProviderHealth,
    ProviderOptions,
    ProviderRegistry,
    RichTextCapability,
    StatusCallbackCapability,
)
from .queue import DeliveryJob, DeliveryQueue, QueueRegistry
from .state import (
    DeliveryRecord,
    DeliveryState,
    DeliveryStateMachine,
    StateStore,
)
from .telemetry import CommunicationTelemetry, append_prometheus_metrics
from .templates import (
    HtmlRenderer,
    MarkdownV2Renderer,
    PlainRenderer,
    RenderedContent,
    Renderer,
    Template,
    TemplateEngine,
)

logger = logging.getLogger("gula.communication")


def build_communication_center(
    config: CommunicationConfig | None = None,
    *,
    providers: ProviderRegistry | None = None,
    policies: PolicyEngine | None = None,
    templates: TemplateEngine | None = None,
    audit: AuditSink | None = None,
    state_store: StateStore | None = None,
    queues: QueueRegistry | None = None,
    event_policies: EventPolicyRegistry | None = None,
) -> CommunicationCenter:
    """Composition root: assemble a fully wired Communication Center.

    Every collaborator is injectable (Dependency Inversion); defaults are
    safe no-op implementations. Provider registration is NOT done here —
    provider plugins register through ``plugins``/``providers``.
    """
    resolved = config or CommunicationConfig.from_env()
    audit_sink: AuditSink = audit or NullAuditSink()
    if resolved.audit_enabled and isinstance(audit_sink, NullAuditSink):
        composite = CompositeAuditSink()
        composite.add(LoggingAuditSink())
        audit_sink = composite

    center = CommunicationCenter(
        providers=providers,
        policies=policies,
        templates=templates,
        audit=audit_sink,
        state_store=state_store,
        queues=queues,
        event_policies=event_policies,
    )
    logger.info(
        "communication_center_built enabled=%s audit=%s policies=%d templates=%d",
        resolved.enabled,
        resolved.audit_enabled,
        len(center.policies.list_policies()),
        len(center.templates.list_templates()),
    )
    return center


__all__ = [
    "ENTRY_POINT_GROUP",
    "MANDATORY_PRIORITY",
    "AlertCapability",
    "Attachment",
    "AuditAction",
    "AuditEvent",
    "AuditSink",
    "BulkCapability",
    "ChannelAttempt",
    "ChannelCapability",
    "ChannelProvider",
    "CommunicationCenter",
    "CommunicationConfig",
    "CommunicationEventHandler",
    "CommunicationTelemetry",
    "CompositeAuditSink",
    "ContentFormat",
    "DeliveryJob",
    "DeliveryQueue",
    "DeliveryReceipt",
    "DeliveryRecord",
    "DeliveryState",
    "DeliveryStateMachine",
    "EventBridge",
    "EventPolicyRegistry",
    "HtmlRenderer",
    "LoggingAuditSink",
    "MarkdownV2Renderer",
    "MediaCapability",
    "NullAuditSink",
    "OutboundMessage",
    "PlainRenderer",
    "PluginManager",
    "PluginMetadata",
    "PluginState",
    "Policy",
    "PolicyDecision",
    "PolicyEngine",
    "PreferenceStore",
    "Priority",
    "ProviderDeliveryResult",
    "ProviderHealth",
    "ProviderOptions",
    "ProviderPlugin",
    "ProviderRegistry",
    "QueueRegistry",
    "Recipient",
    "RecipientPreferences",
    "RenderedContent",
    "Renderer",
    "RichTextCapability",
    "StateStore",
    "StatusCallbackCapability",
    "Template",
    "TemplateEngine",
    "append_prometheus_metrics",
    "build_communication_center",
    "new_delivery_id",
]