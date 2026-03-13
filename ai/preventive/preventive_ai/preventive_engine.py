from preventive_rules import PREVENTIVE_RULES


def suggest_tests(age, gender):

    suggestions = []

    for rule in PREVENTIVE_RULES:

        if age >= rule["age_min"] and gender == rule["gender"]:

            suggestions.extend(rule["tests"])

    return list(set(suggestions))
