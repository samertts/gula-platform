def recommend_tests(age, gender):

    tests = []

    if age > 40:
        tests.append("HbA1c")
        tests.append("Lipid Profile")

    if age > 50:
        tests.append("PSA")

    if gender == "female":
        tests.append("Iron")
        tests.append("Vitamin D")

    return tests
