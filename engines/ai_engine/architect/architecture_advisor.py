import os

PROJECT_ROOT = os.path.expanduser("~/lab-platform")


def suggest_improvements():

    suggestions = []

    device_engine = os.path.join(PROJECT_ROOT, "device_engine")

    if os.path.isdir(device_engine):
        files = os.listdir(device_engine)

        if "tests" not in files:
            suggestions.append("Add tests folder for device_engine")

    smart_catalog = os.path.join(PROJECT_ROOT, "smart_catalog")

    if not os.path.isdir(smart_catalog):
        suggestions.append("Create smart_catalog module")

    return suggestions


if __name__ == "__main__":

    s = suggest_improvements()

    print("\nAI Architecture Suggestions")
    print("---------------------------")

    if not s:
        print("Architecture looks good")

    for i in s:
        print("-", i)
