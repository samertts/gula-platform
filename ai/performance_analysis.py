def analyze_lab_performance(test_count, error_count):

    error_rate = error_count / test_count

    if error_rate > 0.05:
        return "High error rate"

    if error_rate > 0.02:
        return "Moderate error rate"

    return "Good performance"
