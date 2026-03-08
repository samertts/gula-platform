from prevalence_analysis import test_frequency
from trend_analysis import rising_test


def dashboard():

    stats = test_frequency()

    print("\nPopulation Health Dashboard")
    print("----------------------------")

    for test, count in stats.items():

        print(test, "tests:", count)

        trend = rising_test(test)

        print("Trend:", trend)
        print()
