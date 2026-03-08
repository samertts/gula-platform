from clinical_engine import analyze_patient

nhid = "NH123"

alerts = analyze_patient(nhid)

print("\nClinical Decision Alerts")

for a in alerts:
    print(a)
