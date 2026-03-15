from ai_engine.platform_brain.log_collector import read_logs
from network_orchestrator.lab_registry import load_labs


def collect_metrics():

    labs = load_labs()
    logs = read_logs()

    online = 0
    offline = 0

    for lab in labs:
        if lab["status"] == "online":
            online += 1
        else:
            offline += 1

    errors = 0
    warnings = 0

    for l in logs:
        if l["level"] == "ERROR":
            errors += 1
        if l["level"] == "WARNING":
            warnings += 1

    return {
        "labs_online": online,
        "labs_offline": offline,
        "errors": errors,
        "warnings": warnings,
    }
