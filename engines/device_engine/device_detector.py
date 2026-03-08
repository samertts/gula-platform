from drivers import cbc_analyzer, chemistry_analyzer


def detect_device(data):

    if cbc_analyzer.detect(data):
        return "cbc", cbc_analyzer

    if chemistry_analyzer.detect(data):
        return "chemistry", chemistry_analyzer

    return "unknown", None
