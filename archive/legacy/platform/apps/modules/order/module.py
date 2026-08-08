from platform.core.modules import module


@module(
    name="gula.order",
    version="1.0.0",
    description="Order management",
    dependencies=["gula.patient"],
    events_published=["order.created", "order.status_changed", "order.cancelled"],
    events_subscribed=["order.created", "order.status_changed"],
    commands_handled=["create_order", "update_order_status", "cancel_order"],
    queries_handled=["get_order", "list_orders_by_patient"],
)
class OrderModule:
    def __init__(self, order_service=None, audit_service=None, notification_service=None):
        self._order_service = order_service
        self._audit_service = audit_service
        self._notification_service = notification_service
        self.register_service("order_service", order_service)

    async def on_initialize(self) -> None:
        pass

    async def on_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass
