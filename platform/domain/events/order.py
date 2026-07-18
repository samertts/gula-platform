from platform.core.event_bus import Event


class OrderCreated(Event):
    def __init__(self, data: dict):
        super().__init__(topic="order.created", data=data)


class OrderStatusChanged(Event):
    def __init__(self, data: dict):
        super().__init__(topic="order.status_changed", data=data)


class OrderCancelled(Event):
    def __init__(self, data: dict):
        super().__init__(topic="order.cancelled", data=data)
