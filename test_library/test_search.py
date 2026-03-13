from global_tests import GLOBAL_TESTS


def find_test(name):

    for panel in GLOBAL_TESTS:

        for test in panel["tests"]:

            if test["name"].lower() == name.lower():

                return {
                    "test": test["name"],
                    "panel": panel["name"],
                    "normal_range": test["normal_range"],
                }

    return None


def list_all_tests():

    tests = []

    for panel in GLOBAL_TESTS:

        for test in panel["tests"]:

            tests.append(test["name"])

    return tests
