import os

PROJECT_ROOT = os.path.expanduser("~/lab-platform")

REQUIRED_DIRS = ["device_engine", "test_library", "smart_catalog", "ai_engine"]

REQUIRED_FILES = [
    "device_engine/device_listener.py",
]


def scan_directories():
    missing = []
    for d in REQUIRED_DIRS:
        path = os.path.join(PROJECT_ROOT, d)
        if not os.path.isdir(path):
            missing.append(d)
    return missing


def scan_files():
    missing = []
    for f in REQUIRED_FILES:
        path = os.path.join(PROJECT_ROOT, f)
        if not os.path.isfile(path):
            missing.append(f)
    return missing


def count_python_files():
    count = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for f in files:
            if f.endswith(".py"):
                count += 1
    return count


def analyze():
    report = {}

    report["missing_directories"] = scan_directories()
    report["missing_files"] = scan_files()
    report["python_files"] = count_python_files()

    return report


if __name__ == "__main__":
    result = analyze()

    print("\nAI Architect Report")
    print("-------------------")

    print("Python files:", result["python_files"])

    if result["missing_directories"]:
        print("Missing directories:", result["missing_directories"])
    else:
        print("All core directories present")

    if result["missing_files"]:
        print("Missing files:", result["missing_files"])
    else:
        print("All core files present")
