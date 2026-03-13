
def analyze(result):

    value = result.get("value")

    if value > 200:

        return "CRITICAL"

    if value > 150:

        return "HIGH"

    return "NORMAL"
