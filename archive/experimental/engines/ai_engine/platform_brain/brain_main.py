from brain_advisor import get_advice
from brain_analyzer import analyze_logs

if __name__ == "__main__":

    print("\nAI Platform Brain Report")
    print("------------------------")

    report = analyze_logs()

    print("Errors:", report["errors"])
    print("Warnings:", report["warnings"])
    print("Status:", report["status"])

    print("\nAI Advice")

    advice = get_advice()

    for a in advice:
        print("-", a)
