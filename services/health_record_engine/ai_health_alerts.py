from ai_health_analysis import analyze_trend


def health_alert(nhid, test):

    trend = analyze_trend(nhid, test)

    if trend == "Rising":
        return "⚠ Health indicator rising"

    if trend == "Falling":
        return "✔ Improvement detected"

    return "No alert"
