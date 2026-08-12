from prevalence_analysis import test_frequency
from trend_analysis import rising_test


def dashboard():

    stats = test_frequency()


    for test, _count in stats.items():


        rising_test(test)

