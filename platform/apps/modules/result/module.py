from platform.core.modules import module


@module(
    name="gula.result",
    version="1.0.0",
    description="Result management",
    dependencies=["gula.order"],
    events_published=["result.created", "result.validated", "result.corrected"],
    events_subscribed=["result.created", "result.validated"],
    commands_handled=["create_result", "validate_result", "correct_result"],
    queries_handled=["get_result", "list_results_by_order"],
)
class ResultModule:
    def __init__(self, result_service=None, audit_service=None):
        self._result_service = result_service
        self._audit_service = audit_service
        self.register_service("result_service", result_service)

    async def on_initialize(self) -> None:
        pass

    async def on_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass
