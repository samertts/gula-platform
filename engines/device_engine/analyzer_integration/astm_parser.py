def parse_astm(message):

    lines = message.split("|")

    result = {}

    if len(lines) > 3:

        result["test"] = lines[3]

        result["value"] = lines[4]

    return result
