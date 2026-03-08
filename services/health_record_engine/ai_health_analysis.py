from record_reader import get_patient_history


def analyze_trend(nhid, test):

    history = get_patient_history(nhid)

    values = []

    for r in history:
        if r["test"] == test:
            try:
                values.append(float(r["value"]))
            except:
                pass

    if len(values) < 2:
        return "Not enough data"

    if values[-1] > values[-2]:
        return "Rising"

    if values[-1] < values[-2]:
        return "Falling"

    return "Stable"
