from alert_db import load_alerts, save_alerts


def detect_risk(result):

    alerts = load_alerts()

    if result["status"] != "NORMAL":

        alert = {
            "patient_id": result["patient_id"],
            "test": result["test"],
            "value": result["value"],
            "status": result["status"],
            "message": "Abnormal Result Detected",
        }

        alerts.append(alert)

        save_alerts(alerts)

        return alert

    return None
