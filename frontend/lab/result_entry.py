from ai_result_analyzer import analyze
from result_db import load_results, save_results


def add_result(patient_id, test, value):

    results = load_results()

    status = analyze(test, value)

    result = {"patient_id": patient_id, "test": test, "value": value, "status": status}

    results.append(result)

    save_results(results)

    return result
