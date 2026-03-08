from data_loader import load_data


def most_requested_tests():

    data = load_data()

    stats = {}

    for r in data:

        test = r["test"]

        stats[test] = stats.get(test, 0) + 1

    ranked = sorted(stats.items(), key=lambda x: x[1], reverse=True)

    return ranked[:10]
