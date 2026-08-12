def detect(data):
    """
    يحدد هل البيانات صادرة من جهاز CBC
    """
    keywords = ["WBC", "RBC", "HGB", "PLT"]
    for k in keywords:
        if k in data:
            return True
    return False


def parse(data):
    """
    تحويل البيانات إلى نتائج منظمة
    """
    results = []

    lines = data.split("\n")

    for line in lines:
        if "=" in line:
            t, v = line.split("=")

            results.append({"test": t.strip(), "value": v.strip()})

    return results
