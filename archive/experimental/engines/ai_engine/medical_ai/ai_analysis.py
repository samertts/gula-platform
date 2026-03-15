from result_validator import validate_result


def analyze_results(results):

    report = []

    for r in results:

        status = validate_result(r["test"], r["value"])

        report.append({"test": r["test"], "value": r["value"], "status": status})

    return report
