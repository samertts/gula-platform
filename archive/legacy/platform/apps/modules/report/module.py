from platform.core.modules import module


@module(
    name="gula.report",
    version="1.0.0",
    description="Reporting and analytics",
    dependencies=["gula.order", "gula.result"],
    events_published=["report.generated"],
    events_subscribed=[],
    commands_handled=["generate_report", "schedule_report"],
    queries_handled=["get_report", "list_reports"],
)
class ReportModule:
    def __init__(self):
        self.register_service("report_service", None)

    async def on_initialize(self) -> None:
        pass

    async def on_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass
