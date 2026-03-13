def detect(data):
    keywords = ["GLU", "ALT", "AST", "CREA", "UREA", "CHOL"]
    for k in keywords:
        if k in data:
            return True
    return False

def parse(data):
    results = []
    lines = data.split("\n")
    for line in lines:
        if ":" in line:
            parts = line.split(":")
            test = parts[0].strip()
            value = parts[1].strip()
            results.append({
                "test": test,
                "value": value
            })
    return results
