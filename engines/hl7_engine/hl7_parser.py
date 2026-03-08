
def parse_hl7(message):

    segments = message.split("\n")

    data = {}

    for seg in segments:

        parts = seg.split("|")

        data[parts[0]] = parts[1:]

    return data
