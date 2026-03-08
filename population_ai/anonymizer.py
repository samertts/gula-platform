def anonymize(records):

    cleaned = []

    for r in records:

        cleaned.append({"test": r["test"], "value": r["value"], "date": r["date"]})

    return cleaned
