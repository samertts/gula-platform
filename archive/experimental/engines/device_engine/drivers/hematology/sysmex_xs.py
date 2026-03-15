from drivers.registry import register


class SysmexXS:

    name = "Sysmex Hematology"

    @staticmethod
    def detect(data):
        keywords = ["WBC", "RBC", "HGB", "PLT"]
        for k in keywords:
            if k in data:
                return True
        return False

    @staticmethod
    def parse(data):

        results = []

        lines = data.split("\n")

        for line in lines:
            if "=" in line:
                t, v = line.split("=")

                results.append({"test": t.strip(), "value": v.strip()})

        return results


register(SysmexXS)
