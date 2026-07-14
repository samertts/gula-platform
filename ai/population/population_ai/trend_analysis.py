import contextlib

from anonymizer import anonymize
from data_loader import load_health_data


def rising_test(test):

    data = load_health_data()
    data = anonymize(data)

    values = []

    for r in data:

        if r["test"] == test:

            with contextlib.suppress(BaseException):
                values.append(float(r["value"]))

    if len(values) < 2:
        return "Not enough data"

    avg = sum(values) / len(values)

    if avg > 120:
        return "Possible increase trend"

    return "Normal trend"
