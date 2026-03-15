from catalog_engine import get_test_info


def generate_report(results, gender="male"):

    report = []

    for r in results:

        info = get_test_info(r["test"], gender)

        if not info:
            continue

        report.append(
            {
                "test": r["test"],
                "name": info["name"],
                "value": r["value"],
                "unit": info["unit"],
                "normal_range": info["normal_range"],
            }
        )

    return report
