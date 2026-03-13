def analyze_lab_result(test_name, value, min_value, max_value):

    result = {"status": "NORMAL", "message": None}

    if value < min_value:
        result["status"] = "LOW"
        result["message"] = "Result below reference range"

    elif value > max_value:
        result["status"] = "HIGH"
        result["message"] = "Result above reference range"

    # Critical alerts

    if test_name == "Glucose" and value > 400:
        result["status"] = "CRITICAL"
        result["message"] = "Critical glucose level"

    if test_name == "Hemoglobin" and value < 7:
        result["status"] = "CRITICAL"
        result["message"] = "Severe anemia suspected"

    return result
