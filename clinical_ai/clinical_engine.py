from clinical_rules import CLINICAL_RULES
from patient_data_loader import load_patient_data


def analyze_patient(nhid):

    history = load_patient_data(nhid)

    alerts = []

    for record in history:

        for rule in CLINICAL_RULES:

            if record["test"] == rule["test"]:

                try:
                    value = float(record["value"])
                except:
                    continue

                if value >= rule["threshold"]:

                    alerts.append(
                        {
                            "rule": rule["name"],
                            "message": rule["message"],
                            "value": value,
                        }
                    )

    return alerts
