def parse_hl7(message):

    segments = message.split("\r")

    data = {}

    for s in segments:

        parts = s.split("|")

        if parts[0] == "OBX":

            data["test"] = parts[3]

            data["value"] = parts[5]

    return data
