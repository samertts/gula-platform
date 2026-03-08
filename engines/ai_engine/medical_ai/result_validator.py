from engines.ai_engine.medical_ai.medical_ranges import NORMAL_RANGES


def validate_result(test, value):

    if test not in NORMAL_RANGES:
        return "unknown test"

    low, high = NORMAL_RANGES[test]

    try:
        value = float(value)
    except:
        return "invalid value"

    if value < low:
        return "LOW"

    if value > high:
        return "HIGH"

    return "NORMAL"
