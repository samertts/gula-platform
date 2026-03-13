from drivers.registry import register


class RocheCobas:

    name = "Roche Cobas Chemistry"

    @staticmethod
    def detect(data):

        keywords = ["GLU", "ALT", "AST", "CREA"]

        for k in keywords:
            if k in data:
                return True

        return False

    @staticmethod
    def parse(data):

        results = []

        lines = data.split("\n")

        for line in lines:
            if ":" in line:

                t, v = line.split(":")

                results.append({"test": t.strip(), "value": v.strip()})

        return results


register(RocheCobas)
