
from platform.core.kernel import Kernel

from fastapi import APIRouter
from starlette.responses import PlainTextResponse

router = APIRouter()


@router.get("/prometheus")
async def prometheus_metrics() -> PlainTextResponse:
    kernel = Kernel.instance()
    metrics_collector = kernel.container().get("metrics_collector")
    lines = ["# HELP gula_platform_info Platform information", "# TYPE gula_platform_info gauge"]
    lines.append(f'gula_platform_info{{version="{kernel.config.version}",env="{kernel.config.environment}"}} 1')
    lines.append("")
    if metrics_collector:
        snap = metrics_collector.snapshot()
        for name, values in snap.get("counters", {}).items():
            lines.append(f"# HELP gula_{name} Counter metric")
            lines.append(f"# TYPE gula_{name} counter")
            for label_str, val in values.items():
                lines.append(f"gula_{name} {val}")
        for name, values in snap.get("gauges", {}).items():
            lines.append(f"# HELP gula_{name} Gauge metric")
            lines.append(f"# TYPE gula_{name} gauge")
            for label_str, val in values.items():
                lines.append(f"gula_{name} {val}")
        for name, hist in snap.get("histograms", {}).items():
            lines.append(f"# HELP gula_{name} Histogram metric")
            lines.append(f"# TYPE gula_{name} histogram")
            for label_str, stats in hist.items():
                lines.append(f"gula_{name}_sum {stats['sum']}")
                lines.append(f"gula_{name}_count {stats['count']}")
    lines.append("")
    for name, comp in kernel.health._components.items():
        status_val = {"green": 1, "yellow": 0.5, "red": 0, "unknown": -1}.get(comp.status.value, -1)
        lines.append("# HELP gula_health_component Health check status")
        lines.append("# TYPE gula_health_component gauge")
        lines.append(f'gula_health_component{{name="{name}"}} {status_val}')
    return PlainTextResponse("\n".join(lines) + "\n")
