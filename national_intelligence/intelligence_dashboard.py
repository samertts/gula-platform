from disease_patterns import detect_patterns
from outbreak_detector import detect_alerts


def dashboard():

    print("\nNational Health Intelligence Center")
    print("------------------------------------")

    print("\nTest Distribution:")

    stats = detect_patterns()

    for t, c in stats.items():
        print(t, "->", c)

    print("\nAlerts:")

    alerts = detect_alerts()

    if not alerts:
        print("No alerts detected")

    for a in alerts:
        print(a)
