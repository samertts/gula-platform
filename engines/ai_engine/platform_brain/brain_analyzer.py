from log_collector import read_logs


def analyze_logs():

    logs = read_logs()

    error_count = 0
    warning_count = 0

    for l in logs:

        if l["level"] == "ERROR":
            error_count += 1

        if l["level"] == "WARNING":
            warning_count += 1

    report = {"errors": error_count, "warnings": warning_count}

    if error_count > 10:
        report["status"] = "SYSTEM UNSTABLE"

    elif warning_count > 10:
        report["status"] = "SYSTEM WARNING"

    else:
        report["status"] = "SYSTEM HEALTHY"

    return report
