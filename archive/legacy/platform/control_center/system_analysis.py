from metrics_collector import collect_metrics


def analyze_system():

    m = collect_metrics()

    status = "HEALTHY"

    if m["errors"] > 20:
        status = "CRITICAL"

    elif m["warnings"] > 20:
        status = "WARNING"

    if m["labs_offline"] > 5:
        status = "NETWORK ISSUE"

    return {"status": status, "metrics": m}
