from anonymizer import anonymize
from data_loader import load_records


def detect_patterns():

    data = anonymize(load_records())

    stats = {}

    for r in data:

        t = r["test"]

        stats[t] = stats.get(t, 0) + 1

    return stats
