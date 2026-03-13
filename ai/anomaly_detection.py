def detect_anomaly(previous_value, new_value):

    if previous_value is None:
        return False

    change = abs(new_value - previous_value)

    if change > (previous_value * 3):
        return True

    return False
