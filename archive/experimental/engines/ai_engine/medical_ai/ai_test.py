from ai_analysis import analyze_results

sample = [
    {"test": "WBC", "value": "6000"},
    {"test": "HGB", "value": "8"},
    {"test": "ALT", "value": "70"},
]

analysis = analyze_results(sample)

for r in analysis:
    print(r)
