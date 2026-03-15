from brain_analyzer import analyze_logs


def get_advice():

    report = analyze_logs()

    advice = []

    if report["errors"] > 10:
        advice.append("Investigate failing services")

    if report["warnings"] > 10:
        advice.append("Check device connectivity")

    if report["status"] == "SYSTEM HEALTHY":
        advice.append("System running normally")

    return advice
