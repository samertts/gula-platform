from catalog_data import CATALOG


def get_test_info(test_code, gender="male"):

    test = CATALOG.get(test_code)

    if not test:
        return None

    return {
        "name": test["name"],
        "unit": test["unit"],
        "normal_range": test["ranges"].get(gender),
    }


def list_tests():

    return list(CATALOG.keys())
