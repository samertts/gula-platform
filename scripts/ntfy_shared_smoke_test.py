from __future__ import annotations

import httpx

from shared.notifications.sender import NotificationSender


def main() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content
        seen["headers"] = dict(request.headers)
        return httpx.Response(204)

    sender = NotificationSender()
    sender._ntfy_base_url = "https://ntfy.example.test"
    sender._ntfy_topic = "gula-ops"
    sender._http_client = httpx.Client(transport=httpx.MockTransport(handler))

    assert sender.send_ntfy("incident=api_latency", title="API degraded", priority="high") is True
    assert seen["url"] == "https://ntfy.example.test/gula-ops"
    assert seen["body"] == b"incident=api_latency"
    assert seen["headers"]["title"] == "API degraded"
    assert seen["headers"]["priority"] == "high"
    sender.close()
    print("shared ntfy smoke test passed")


if __name__ == "__main__":
    main()
