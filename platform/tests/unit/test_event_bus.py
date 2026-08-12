import pytest


class TestEventBus:
    def test_create_topic(self, event_bus):
        topic = event_bus.create_topic("test.events")
        assert topic.name == "test.events"
        assert event_bus.topic_count() == 1

    def test_publish_subscribe(self, event_bus):
        received = []

        async def handler(event):
            received.append(event.data)

        event_bus.subscribe("test.events", handler)
        from platform.core.event_bus import Event
        import asyncio
        asyncio.run(event_bus.publish("test.events", Event(topic="test.events", data={"msg": "hello"})))
        assert len(received) == 1
        assert received[0]["msg"] == "hello"

    def test_subscribe_unknown_topic_creates_it(self, event_bus):
        received = []

        async def handler(event):
            received.append(event)

        event_bus.subscribe("auto.topic", handler)
        assert event_bus.topic_count() == 1

    def test_dead_letter_queue(self, event_bus):
        import pytest

        async def failing_handler(event):
            raise ValueError("fail")

        event_bus.subscribe("failing.topic", failing_handler)
        from platform.core.event_bus import Event

        with pytest.raises(ValueError):
            import asyncio
            asyncio.run(event_bus.publish_with_retry("failing.topic", Event(topic="failing.topic")))
        assert len(event_bus.get_dead_letter_queue()) == 1
        dlq = event_bus.get_dead_letter_queue()
        assert "error" in dlq[0]

    def test_topic_metrics(self, event_bus):
        assert event_bus.subscriber_count() == 0
        assert event_bus.topic_count() == 0

        async def handler(event):
            pass

        event_bus.subscribe("a", handler)
        event_bus.subscribe("b", handler)
        assert event_bus.subscriber_count() == 2
        assert event_bus.topic_count() == 2

    def test_global_subscriber(self, event_bus):
        received = []

        async def global_handler(event):
            received.append(event.topic)

        event_bus.add_global_subscriber(global_handler)
        from platform.core.event_bus import Event
        import asyncio
        asyncio.run(event_bus.publish("any.topic", Event(topic="any.topic")))
        assert "any.topic" in received


class TestEvent:
    def test_event_has_id(self):
        from platform.core.event_bus import Event
        e = Event(topic="test")
        assert e.event_id is not None
        assert len(e.event_id) > 0

    def test_event_default_timestamp(self):
        from platform.core.event_bus import Event
        e = Event(topic="test")
        assert e.timestamp is not None

    def test_event_type_property(self):
        from platform.core.event_bus import Event
        e = Event(topic="test")
        assert e.event_type == "Event"
