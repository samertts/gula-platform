from demand_prediction import predict_next_test
from lab_activity import daily_test_volume
from top_tests import most_requested_tests


def dashboard():

    print("\nLab Business Intelligence Dashboard")
    print("------------------------------------")

    print("\nTop Tests:")

    for t in most_requested_tests():

        print(t)

    print("\nDaily Volume:")

    print(daily_test_volume())

    print("\nPredicted Next High Demand Test:")

    print(predict_next_test())
