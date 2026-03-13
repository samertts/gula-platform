def disease_statistics(results):

    diabetes = 0
    anemia = 0

    for r in results:

        if r["test"] == "HbA1c" and r["value"] > 6.5:
            diabetes += 1

        if r["test"] == "Hemoglobin" and r["value"] < 12:
            anemia += 1

    return {"diabetes_cases": diabetes, "anemia_cases": anemia}
