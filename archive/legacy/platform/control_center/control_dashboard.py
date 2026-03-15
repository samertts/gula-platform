from solution_advisor import suggest_solutions


def dashboard():

    report = suggest_solutions()

    print("\nNational Health Platform Control Center")
    print("---------------------------------------")

    print("\nSystem Status:", report["status"])

    print("\nMetrics:")

    for k, v in report["metrics"].items():
        print(k, ":", v)

    print("\nRecommended Actions:")

    for s in report["solutions"]:
        print("-", s)


if __name__ == "__main__":
    dashboard()
