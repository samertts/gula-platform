from data_loader import load_data


def predict_next_test():

    data = load_data()

    stats = {}

    for r in data:

        t = r["test"]

        stats[t] = stats.get(t, 0) + 1

    return max(stats, key=stats.get)

