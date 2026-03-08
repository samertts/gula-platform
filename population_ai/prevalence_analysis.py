from anonymizer import anonymize
from data_loader import load_health_data


def test_frequency():

    data = load_health_data()
    data = anonymize(data)

    stats = {}

    for r in data:

        t = r["test"]

        stats[t] = stats.get(t, 0) + 1

    return stats
