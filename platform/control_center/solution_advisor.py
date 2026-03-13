from system_analysis import analyze_system


def suggest_solutions():

    report = analyze_system()

    solutions = []

    metrics = report["metrics"]

    if metrics["errors"] > 20:
        solutions.append("Investigate failing services and restart affected modules")

    if metrics["warnings"] > 20:
        solutions.append("Check device connectivity and network latency")

    if metrics["labs_offline"] > 5:
        solutions.append("Contact offline laboratories and verify internet connection")

    if report["status"] == "HEALTHY":
        solutions.append("System operating normally")

    return {"status": report["status"], "solutions": solutions, "metrics": metrics}


def suggest_solutions():

    report = analyze_system()

    solutions = []

    metrics = report["metrics"]

    if metrics["errors"] > 20:
        solutions.append("Investigate failing services and restart affected modules")

    if metrics["warnings"] > 20:
        solutions.append("Check device connectivity and network latency")

    if metrics["labs_offline"] > 5:
        solutions.append("Contact offline laboratories and verify internet connection")

    if report["status"] == "HEALTHY":
        solutions.append("System operating normally")

    return {"status": report["status"], "solutions": solutions, "metrics": metrics}
