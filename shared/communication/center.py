"""Communication Center — the ONLY entry point of the GULA Communication
Platform Core.

Every application request and every consumed event enters here. The Center
orchestrates: policy decision → template render → provider delivery (through
the registry) → state transitions → audit + telemetry. It holds ZERO
knowledge of provider implementations; new providers plug in without any
change to this module (Open/Closed Principle).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from .audit import AuditAction, AuditEvent, AuditSink, NullAuditSink
from .events import EventPolicyRegistry
from .model import (
    ContentFormat,
    DeliveryReceipt,
    OutboundMessage,
    Priority,
    ProviderDeliveryResult,
    Recipient,
    new_delivery_id,
)
from .policy import Policy, PolicyDecision, PolicyEngine, RecipientPreferences
from .providers import (
    AlertCapability,
    ChannelCapability,
    ChannelProvider,
    MediaCapability,
    ProviderHealth,
    ProviderRegistry,
    RichTextCapability,
)
from .queue import DeliveryJob, QueueRegistry
from .state import DeliveryRecord, DeliveryState, DeliveryStateMachine, StateStore
from .telemetry import CommunicationTelemetry
from .templates import TemplateEngine

logger = logging.getLogger("gula.communication.center")


@dataclass(frozen=True)
class _ProviderOptionsImpl:
    """Internal ``ProviderOptions`` implementation carrying resolved values."""

    priority: str
    max_retries: int
    locale: str
    suppress_quiet_hours: bool


class CommunicationCenter:
    """Provider-independent orchestrator for the whole communication stack.

    Dependency injection: every collaborator is passed in; none is imported
    from a provider or infrastructure package.
    """

    def __init__(
        self,
        providers: ProviderRegistry | None = None,
        policies: PolicyEngine | None = None,
        templates: TemplateEngine | None = None,
        audit: AuditSink | None = None,
        state_store: StateStore | None = None,
        queues: QueueRegistry | None = None,
        event_policies: EventPolicyRegistry | None = None,
    ) -> None:
        self.providers = providers or ProviderRegistry()
        self.policies = policies or PolicyEngine()
        self.templates = templates or TemplateEngine()
        self._audit_sink = audit or NullAuditSink()
        self._state_store = state_store
        self._queues = queues or QueueRegistry()
        self.event_policies = event_policies or EventPolicyRegistry()

    @property
    def audit_sink(self) -> AuditSink:
        return self._audit_sink

    # ── Public API ───────────────────────────────────────────────────────────

    def dispatch(
        self,
        recipient: str | Recipient,
        *,
        message: OutboundMessage | None = None,
        policy: Policy | str | None = None,
        variables: dict[str, Any] | None = None,
        template_id: str = "",
        template_version: str = "",
        locale: str = "",
        content: str = "",
        format: ContentFormat = ContentFormat.PLAIN,
        subject: str = "",
        priority: Priority | str = Priority.NORMAL,
        severity: str = "",
        queue: str = "",
        retry_delay_seconds: float = 0.0,
        context: dict[str, Any] | None = None,
    ) -> DeliveryReceipt:
        """Send one message to one recipient through the resolved channels.

        Exactly one of ``message`` or ``template_id``/``content`` must drive
        the payload. Channel routing comes from ``policy`` (a Policy object
        or a registered policy id); without one, a default policy is built
        from ``channel`` overrides passed via ``context``.
        """
        address = recipient.address if isinstance(recipient, Recipient) else recipient
        if not address:
            raise ValueError("recipient is required")
        if message is None and not template_id and not content:
            raise ValueError("message, template_id or content is required")

        pid = new_delivery_id()
        priority_enum = Priority(priority)
        self._audit(
            AuditAction.DISPATCH_CREATED,
            pid,
            {"recipient": address, "policy": self._policy_id(policy), "priority": priority_enum.value},
            "created",
        )

        resolved_policy = self._resolve_policy(policy, priority_enum)
        prefs = RecipientPreferences.unrestricted()
        decision = self.policies.decide(resolved_policy, address, prefs)
        self._audit(
            AuditAction.POLICY_DECISION,
            pid,
            {"policy_id": resolved_policy.id, "decision": decision.to_dict()},
            "decided",
        )

        final_message = message
        if final_message is None:
            rendered = None
            effective_locale = locale or resolved_policy.locale
            if template_id:
                rendered = self.templates.render(
                    template_id,
                    variables or {},
                    version=template_version,
                    locale=effective_locale,
                    format=format if format != ContentFormat.PLAIN else resolved_policy.format,
                    strict=False,
                )
                self._audit(
                    AuditAction.RENDER,
                    pid,
                    {"template_id": template_id, "version": rendered.template_version, "locale": rendered.locale},
                    "rendered",
                )
            final_message = OutboundMessage(
                content=rendered.body if rendered else content,
                format=rendered.format if rendered else format,
                subject=subject or (rendered.subject if rendered else ""),
                locale=effective_locale,
                template_id=template_id,
                template_version=rendered.template_version if rendered else template_version,
                metadata={"context": context or {}},
            )

        if queue:
            result = self._enqueue(pid, address, decision, final_message, priority_enum, queue)
            return result

        return self._deliver_sync(
            pid,
            address,
            decision,
            final_message,
            priority_enum,
            severity,
            retry_delay_seconds,
            context,
        )

    def handle_communication_event(
        self, event_name: str, payload: dict[str, Any]
    ) -> DeliveryReceipt:
        """Consume a platform event and dispatch through its bound policy.

        Returns the delivery receipt so callers (and the event bridge) can
        observe the outcome; unhandled/undeliverable events yield a failed
        receipt rather than a silent ``None``.
        """
        binding = self.event_policies.resolve(event_name)
        if binding is None:
            logger.warning("communication_event_unhandled event=%s", event_name)
            return DeliveryReceipt(
                delivery_id=new_delivery_id(),
                recipient="",
                state=DeliveryState.FAILED.value,
                error=f"no event binding: {event_name}",
            )
        policy_id, recipient_key, metadata_keys = binding
        recipient = payload.get(recipient_key, "")
        if not recipient:
            self._audit(
                AuditAction.FAILED,
                "",
                {"event": event_name, "reason": "no_recipient", "recipient_key": recipient_key},
                "failed",
            )
            return DeliveryReceipt(
                delivery_id=new_delivery_id(),
                recipient="",
                state=DeliveryState.FAILED.value,
                error="event payload had no recipient",
            )
        meta = {key: payload[key] for key in metadata_keys if key in payload}
        policy = self.policies.get(policy_id)
        if policy is None:
            self._audit(AuditAction.FAILED, "", {"event": event_name, "policy": policy_id}, "failed")
            return DeliveryReceipt(
                delivery_id=new_delivery_id(),
                recipient="",
                state=DeliveryState.FAILED.value,
                error=f"unknown policy: {policy_id}",
            )
        CommunicationTelemetry.record_dispatch(policy_id)
        return self.dispatch(
            recipient,
            template_id=policy.template_id,
            policy=policy,
            variables=payload,
            locale=policy.locale,
            format=policy.format,
            priority=policy.priority,
            context={"event_name": event_name, **meta},
        )

    def on_status_change(self, provider_name: str, delivery_ref: str, status: str) -> None:
        """Forward a provider-reported status update to the owning provider."""
        provider = self.providers.get(provider_name)
        if provider is None:
            logger.warning("communication_status_unknown_provider name=%s", provider_name)
            return
        if not self.providers.supports(provider, ChannelCapability.STATUS_CALLBACK):
            return
        on_status_change = provider.on_status_change
        on_status_change(delivery_ref, status)

    def health(self) -> dict[str, Any]:
        """Provider + plugin + queue snapshot for deep health checks."""
        return {
            "providers": self.providers.describe(),
            "channel_count": len(self.providers.channels()),
            "queues": self._queues.names(),
            "policies": len(self.policies.list_policies()),
            "event_bindings": len(self.event_policies.bindings()),
        }

    # ── Internals ────────────────────────────────────────────────────────────

    def _resolve_policy(self, policy: Policy | str | None, priority: Priority) -> Policy:
        if isinstance(policy, Policy):
            return policy
        if isinstance(policy, str):
            found = self.policies.get(policy)
            if found is None:
                raise ValueError(f"unknown policy: {policy}")
            return found
        return Policy(id="default", priority=priority)

    def _policy_id(self, policy: Policy | str | None) -> str:
        if isinstance(policy, Policy):
            return policy.id
        if isinstance(policy, str):
            return policy
        return "default"

    def _enqueue(
        self,
        pid: str,
        address: str,
        decision: PolicyDecision,
        message: OutboundMessage,
        priority: Priority,
        queue: str,
    ) -> DeliveryReceipt:
        queue_provider = self._queues.get(queue)
        if queue_provider is None:
            return DeliveryReceipt(
                delivery_id=pid,
                recipient=address,
                state=DeliveryState.FAILED.value,
                error=f"unknown queue: {queue}",
            )
        from uuid import uuid4

        job = DeliveryJob(
            job_id=uuid4().hex,
            delivery_id=pid,
            recipient=address,
            channel=decision.channels[0] if decision.channels else "",
            message=message,
            priority=priority,
            max_retries=decision.policy.max_retries,
            metadata={"policy_id": decision.policy.id},
        )
        try:
            import asyncio

            coro = queue_provider.enqueue(job)
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(coro)
            else:
                # Already inside an event loop: schedule fire-and-forget.
                asyncio.get_running_loop().create_task(coro)
            self._transition(pid, DeliveryState.CREATED, DeliveryState.QUEUED)
            self._audit(
                AuditAction.DISPATCH_CREATED,
                pid,
                {"queue": queue, "recipient": address},
                "queued",
            )
            return DeliveryReceipt(
                delivery_id=pid,
                recipient=address,
                state=DeliveryState.QUEUED.value,
            )
        except Exception as exc:
            self._transition(pid, DeliveryState.CREATED, DeliveryState.FAILED, str(exc))
            self._audit(AuditAction.FAILED, pid, {"queue": queue, "reason": "enqueue_error"}, "failed")
            return DeliveryReceipt(
                delivery_id=pid,
                recipient=address,
                state=DeliveryState.FAILED.value,
                error=str(exc),
            )

    def _deliver_sync(
        self,
        pid: str,
        address: str,
        decision: PolicyDecision,
        message: OutboundMessage,
        priority: Priority,
        severity: str,
        retry_delay_seconds: float,
        context: dict[str, Any] | None,
    ) -> DeliveryReceipt:
        start = time.monotonic()
        attempts: list[ProviderDeliveryResult] = []
        final_state = DeliveryState.FAILED
        final_error: str | None = None

        # Primary + fallback channels, in plan order.
        channels = decision.channels
        escalated = False
        if not channels:
            self._audit(AuditAction.FAILED, pid, {"reason": "no_channels"}, "failed")
            return DeliveryReceipt(
                delivery_id=pid, recipient=address, state=DeliveryState.FAILED.value,
                error="policy resolved no channels",
            )

        for channel in channels:
            self._transition(pid, DeliveryState.CREATED, DeliveryState.SENDING)
            result = self._deliver_channel(
                pid,
                channel,
                Recipient(address),
                message,
                priority,
                severity,
                retry_delay_seconds,
                decision.policy.max_retries,
            )
            attempts.append(result)
            if result.success:
                self._transition(pid, DeliveryState.SENDING, DeliveryState.DELIVERED)
                final_state = DeliveryState.DELIVERED
                final_error = None
                break
            # A failed channel does not block the next one in the plan
            # (required set first, fallback alternatives after).

        if final_state != DeliveryState.DELIVERED and decision.policy.escalation_channels:
            escalated = True
            CommunicationTelemetry.record_escalation()
            for esc_channel in decision.policy.escalation_channels:
                self._audit(
                    AuditAction.ESCALATION,
                    pid,
                    {"channel": esc_channel, "escalation_after_seconds": decision.policy.escalation_after_seconds},
                    "escalated",
                )
                result = self._deliver_channel(
                    pid,
                    esc_channel,
                    Recipient(address),
                    message,
                    decision.policy.priority,
                    severity,
                    retry_delay_seconds,
                    decision.policy.max_retries,
                )
                attempts.append(result)
                if result.success:
                    self._transition(pid, DeliveryState.SENDING, DeliveryState.DELIVERED)
                    final_state = DeliveryState.DELIVERED
                    final_error = None
                    break

        if final_state == DeliveryState.FAILED and attempts:
            self._transition(pid, DeliveryState.SENDING, DeliveryState.FAILED, final_error)
        CommunicationTelemetry.record_latency(time.monotonic() - start)
        self._audit(
            AuditAction.FAILED if final_state == DeliveryState.FAILED else AuditAction.POLICY_DECISION,
            pid,
            {"state": final_state.value, "escalated": escalated},
            final_state.value,
        )
        return DeliveryReceipt(
            delivery_id=pid,
            recipient=address,
            state=final_state.value,
            attempts=tuple(attempts),
            error=final_error,
        )

    def _deliver_channel(
        self,
        pid: str,
        channel: str,
        recipient: Recipient,
        message: OutboundMessage,
        priority: Priority,
        severity: str,
        retry_delay_seconds: float,
        max_retries: int,
    ) -> ProviderDeliveryResult:
        provider = self._pick_provider(channel)
        if provider is None:
            CommunicationTelemetry.record_attempt(channel, False)
            result = ProviderDeliveryResult(
                success=False,
                channel=channel,
                provider="",
                error=f"no provider registered for channel: {channel}",
                retryable=False,
            )
            self._audit(
                AuditAction.PROVIDER_ATTEMPT,
                pid,
                {"channel": channel, "error": "no_provider"},
                "failed",
            )
            return result

        options = _ProviderOptionsImpl(
            priority=priority.value,
            max_retries=max_retries,
            locale=message.locale,
            suppress_quiet_hours=priority == Priority.MANDATORY,
        )
        attempts = 0
        last: ProviderDeliveryResult | None = None
        while True:
            attempts += 1
            last = self._attempt_delivery(provider, recipient, message, options, severity)
            CommunicationTelemetry.record_attempt(channel, last.success)
            self._audit(
                AuditAction.PROVIDER_ATTEMPT,
                pid,
                {"channel": channel, "provider": provider.name, "attempt": attempts, "success": last.success},
                (last.success and "delivered") or "failed",
            )
            if last.success or not last.retryable or attempts >= (options.max_retries or 1):
                break
            if retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)
        return last

    @staticmethod
    def _attempt_delivery(
        provider: ChannelProvider,
        recipient: Recipient,
        message: OutboundMessage,
        options: _ProviderOptionsImpl,
        severity: str,
    ) -> ProviderDeliveryResult:
        try:
            if severity and isinstance(provider, AlertCapability):
                return provider.deliver_alert(recipient, message, severity, options)
            if message.attachments and isinstance(provider, MediaCapability):
                return provider.deliver_media(recipient, message, options)
            if message.format in (ContentFormat.HTML, ContentFormat.MARKDOWN) and isinstance(
                provider, RichTextCapability,
            ):
                return provider.deliver_rich(recipient, message, options)
            return provider.deliver(recipient, message, options)
        except Exception as exc:
            logger.error(
                "communication_provider_exception provider=%s error_type=%s",
                provider.name,
                type(exc).__name__,
            )
            communication = getattr(provider, "channel", "unknown")
            return ProviderDeliveryResult(
                success=False,
                channel=communication,
                provider=provider.name,
                error=f"{type(exc).__name__}: {exc}",
                retryable=False,
            )

    def _pick_provider(self, channel: str) -> ChannelProvider | None:
        for provider in self.providers.providers_for(channel):
            try:
                health = provider.health()
            except Exception:
                health = ProviderHealth.DOWN
            if health != ProviderHealth.DOWN:
                return provider
        return None

    def _transition(
        self,
        pid: str,
        current: DeliveryState,
        target: DeliveryState,
        error: str | None = None,
    ) -> None:
        DeliveryStateMachine.transition(current, target)
        if self._state_store is not None:
            record = DeliveryRecord(
                delivery_id=pid,
                recipient="",
                state=target,
                error=error,
                updated_at=time.monotonic(),
            )
            self._state_store.save(record)
        self._audit(
            AuditAction.STATE_TRANSITION,
            pid,
            {"from": current.value, "to": target.value},
            target.value,
        )

    def _audit(self, action: AuditAction, delivery_id: str, context: dict[str, Any], outcome: str) -> None:
        try:
            self._audit_sink.record(AuditEvent(action=action, delivery_id=delivery_id, context=context, outcome=outcome))
        except Exception:
            logger.exception("communication_audit_failed action=%s", action.value)


__all__ = ["CommunicationCenter"]