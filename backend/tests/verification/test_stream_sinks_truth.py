"""A stream sink does not report records it never delivered.

IA-072, the item IA-071 left open. Three of the four sinks in
``app/health_data/streaming/sinks.py`` logged "writing N records to
<destination>" and then ``return len(records)``. The record count *is* this
interface's success value — ``Sink.write`` is annotated ``-> int`` and
``WebSocketSink`` returns the number actually delivered — so returning
``len(records)`` claimed full delivery of a batch that went nowhere. None of
the three ever used the connection string, host or bucket it was given.

``ObjectStoreSink`` was the most deceptive: it built a real filename,
serialised the batch with ``json.dumps`` and logged the exact byte count, so
its log line looked like evidence of a completed upload.

``WebSocketSink`` is the one real sink and is deliberately untouched.

Reachability: latent. Nothing outside the package constructs any of these.
This is an exported surface that would have lost its first consumer's data
silently, which is why it is repaired now rather than after someone wires a
health-data stream to it.

RATCHET. The regression here is not an exception coming back — it is someone
making a sink "work" by returning the count again. The tests assert the raise,
assert the count is not returned, and assert the real sink still delivers.
"""
from __future__ import annotations

import ast
import asyncio
import pathlib

import pytest

SINKS_FILE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app" / "health_data" / "streaming" / "sinks.py"
)

FAKE_SINKS = ("PostgresSink", "ClickHouseSink", "ObjectStoreSink")
REAL_SINK = "WebSocketSink"

RECORDS = [{"patient": "p-1", "value": 5.4}, {"patient": "p-2", "value": 6.1}]


def _sink(name):
    from app.health_data.streaming import sinks

    return getattr(sinks, name)


@pytest.mark.parametrize("name", FAKE_SINKS)
def test_an_unimplemented_sink_refuses_instead_of_reporting_delivery(name):
    from app.health_data.streaming.sinks import StreamSinkUnavailable

    with pytest.raises(StreamSinkUnavailable) as caught:
        asyncio.run(_sink(name)().write(RECORDS))

    message = str(caught.value)
    assert name in message
    assert "not implemented" in message
    # the refusal names the batch size, so an operator can see what was lost
    assert str(len(RECORDS)) in message


@pytest.mark.parametrize("name", FAKE_SINKS)
def test_an_unimplemented_sink_never_returns_the_record_count(name):
    """The specific fake success: `return len(records)` means "all delivered"."""
    from app.health_data.streaming.sinks import StreamSinkUnavailable

    try:
        result = asyncio.run(_sink(name)().write(RECORDS))
    except StreamSinkUnavailable:
        return
    pytest.fail(f"{name}.write returned {result!r} for records it did not deliver")


def test_the_websocket_sink_still_delivers_and_counts_honestly():
    """The control. If the repair had been applied too broadly, this would fail.

    WebSocketSink returns the number of records it actually sent, and drops
    connections that raise. Both behaviours are asserted so the one real sink
    cannot be quietly converted into a refusal alongside the others.
    """
    from app.health_data.streaming.sinks import WebSocketSink

    sent: list[str] = []

    class GoodConnection:
        async def send(self, payload: str) -> None:
            sent.append(payload)

    class BrokenConnection:
        async def send(self, payload: str) -> None:
            raise ConnectionError("peer gone")

    sink = WebSocketSink()
    asyncio.run(sink.register_connection(GoodConnection()))
    asyncio.run(sink.register_connection(BrokenConnection()))

    delivered = asyncio.run(sink.write(RECORDS))

    assert delivered == len(RECORDS), delivered
    assert len(sent) == len(RECORDS)
    # the broken connection was dropped, the good one kept
    assert len(sink._connections) == 1


def test_no_sink_returns_len_records_without_delivering():
    """Source-level ratchet over the whole file.

    A `return len(records)` in a sink that never awaits anything on a
    destination is the exact shape of this defect.
    """
    source = SINKS_FILE.read_text()
    tree = ast.parse(source)

    offenders, scanned = [], 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for method in node.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if method.name != "write":
                continue
            scanned += 1
            body = ast.get_source_segment(source, method) or ""
            if "return len(records)" in body and "await" not in body:
                offenders.append(f"{node.name}.write returns len(records) without awaiting a destination")

    # 4 sinks define write, plus the ABC declaration
    assert scanned >= 4, f"only {scanned} write methods scanned; the scan has gone blind"
    assert not offenders, "\n".join(offenders)
