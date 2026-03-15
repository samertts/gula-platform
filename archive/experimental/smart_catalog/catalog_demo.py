from report_generator import generate_report

sample_results = [
    {"test": "WBC", "value": "6200"},
    {"test": "RBC", "value": "4.8"},
    {"test": "HGB", "value": "13.4"},
    {"test": "ALT", "value": "25"},
]

report = generate_report(sample_results)

for r in report:
    print(r)
