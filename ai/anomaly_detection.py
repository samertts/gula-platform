def detect_anomaly(previous_value, new_value):

    if previous_value is None:
        return False

    change = abs(new_value - previous_value)

    return change > previous_value * 3
