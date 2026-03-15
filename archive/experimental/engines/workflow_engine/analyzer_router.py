analyzers = {
    "hematology": ["CBC", "HGB", "RBC"],
    "chemistry": ["GLU", "ALT", "AST"],
    "immunology": ["TSH", "T3", "T4"],
}


def route_test(test_code):

    for analyzer, tests in analyzers.items():

        if test_code in tests:
            return analyzer

    return "manual"
