from data_loader import load_data


def daily_test_volume():

    data = load_data()

    volume = {}

    for r in data:

        d = r["date"]

        volume[d] = volume.get(d, 0) + 1

    return volume
