def parse_device_data(raw_data):
    results = []

    lines = raw_data.split("\n")

    for line in lines:
        if "=" in line:
            parts = line.split("=")
            test = parts[0].strip()
            value = parts[1].strip()

            results.append({"test_code": test, "value": value})

    return results
