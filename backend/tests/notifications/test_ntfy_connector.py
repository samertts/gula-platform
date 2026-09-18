from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

# NR-124. This read `from backend.app...`, which is the shadow root
# NR-056 and NR-058 exist to keep out of the tree: it loads a SECOND copy
# of the module and everything it imports, each with its own state. It
# also polluted sys.modules for the rest of the session, which is what
# made test_capability_import_roots fail in company and pass alone.
from app.integration.connectors.ntfy import NtfyConnector


@pytest.mark.asyncio
async def test_ntfy_send_posts_plain_text_with_safe_headers() -> None:
    connector = NtfyConnector(
        config={
            "base_url": "https://ntfy.example.test",
            "topic": "gula-ops",
        },
    )
    response = Mock(is_success=True, status_code=200, text="")
    connector._client = AsyncMock()
    connector._client.post.return_value = response
    connector._connected = True

    result = await connector.send(
        {
            "title": "API degraded",
            "message": "incident=api_latency status=degraded",
            "priority": "high",
            "tags": "warning",
        },
    )

    assert result["success"] is True
    assert result["provider"] == "ntfy"
    connector._client.post.assert_awaited_once()
    url, kwargs = connector._client.post.await_args.args[0], connector._client.post.await_args.kwargs
    assert url == "https://ntfy.example.test/gula-ops"
    assert kwargs["content"] == b"incident=api_latency status=degraded"
    assert kwargs["headers"]["Title"] == "API degraded"
    assert kwargs["headers"]["Priority"] == "high"
    assert kwargs["headers"]["Tags"] == "warning"


@pytest.mark.asyncio
async def test_ntfy_rejects_empty_message_without_network_call() -> None:
    connector = NtfyConnector(config={})
    connector._client = AsyncMock()
    connector._connected = True

    result = await connector.send({"message": "   "})

    assert result == {
        "success": False,
        "error": "message required",
        "provider": "ntfy",
    }
    connector._client.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_ntfy_rejects_oversized_message_without_network_call() -> None:
    connector = NtfyConnector(config={})
    connector._client = AsyncMock()
    connector._connected = True

    result = await connector.send({"message": "x" * 4097})

    assert result["success"] is False
    assert result["error"] == "message exceeds 4096 characters"
    connector._client.post.assert_not_awaited()
