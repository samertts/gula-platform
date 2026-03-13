from disease_patterns import detect_patterns


def detect_alerts():

    stats = detect_patterns()

    alerts = []

    for test, count in stats.items():

        if count > 200:  # عتبة مثال

            alerts.append({"test": test, "message": "High volume detected"})

    return alerts
