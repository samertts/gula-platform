"""Shared helpers for webhook-based provider plugins (PROGRAM-COMM-002).

Discord / Slack / Teams / generic webhook plugins share: webhook URL
resolution (env → docker/k8s secrets), attachment resolution (local path or
HTTP(S) URL → bytes), and a transport wiring helper. No Core involvement.
"""

from __future__ import annotations

import os
from typing import Any

from shared.communication.model import Attachment

from ..base import ProviderMetrics, ProviderSettings, Redactor
from ..secrets import SecretResolver
from ..transport import CircuitBreaker, HttpTransport, TokenBucket, TransportSettings


def build_transport(
    settings: ProviderSettings,
    *,
    redactor: Redactor,
    http_client: Any = None,
    rate_per_minute: int | None = None,
) -> HttpTransport:
    """Build an HttpTransport sharing the provider's redactor/metrics."""
    return HttpTransport(
        name=settings.name,
        settings=TransportSettings(
            timeout_seconds=settings.timeout_seconds,
            max_retries=settings.max_retries,
            backoff_base_seconds=settings.backoff_base_seconds,
            backoff_max_seconds=settings.backoff_max_seconds,
            rate_per_minute=rate_per_minute or settings.rate_per_minute,
            circuit_failure_threshold=settings.circuit_failure_threshold,
            circuit_recovery_timeout=settings.circuit_recovery_timeout,
        ),
        http_client=http_client,
        redactor=redactor,
        rate_limiter=TokenBucket(rate_per_minute or settings.rate_per_minute),
        circuit_breaker=CircuitBreaker(name=f"provider:{settings.name}"),
        metrics=ProviderMetrics(settings.name),
    )


def resolve_webhook_url(
    kind: str,
    resolver: SecretResolver | None = None,
) -> str:
    """Resolve a webhook URL from env / docker / k8s / cloud secrets."""
    resolver = resolver or SecretResolver()
    from ..secrets import webhook_secret_name

    return resolver.resolve(webhook_secret_name(kind))


def attachment_bytes(attachment: Attachment) -> bytes:
    """Read an attachment reference (local path or HTTP(S) URL) into bytes."""
    reference = attachment.reference
    if reference.startswith(("http://", "https://")):
        import httpx

        with httpx.Client(timeout=30.0) as client:
            response = client.get(reference)
            if response.status_code >= 300:
                raise OSError(f"attachment fetch failed: {response.status_code}")
            return response.content
    with open(reference, "rb") as fh:
        return fh.read()


def attachment_filename(attachment: Attachment) -> str:
    """Best-effort filename from the attachment reference."""
    if attachment.name:
        return attachment.name
    return os.path.basename(attachment.reference.rstrip("/")) or "attachment.bin"


def is_http_reference(value: str) -> bool:
    return value.startswith(("http://", "https://"))


__all__ = [
    "attachment_bytes",
    "attachment_filename",
    "build_transport",
    "is_http_reference",
    "resolve_webhook_url",
]
