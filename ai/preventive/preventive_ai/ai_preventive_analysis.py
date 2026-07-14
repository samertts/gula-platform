from health_record_engine.record_reader import get_patient_history
from preventive_engine import suggest_tests


def smart_preventive_plan(nhid, age, gender):

    history = get_patient_history(nhid)

    done_tests = []

    for r in history:
        done_tests.append(r["test"])

    suggestions = suggest_tests(age, gender)

    needed = []

    for t in suggestions:

        if t not in done_tests:
            needed.append(t)

    return needed
