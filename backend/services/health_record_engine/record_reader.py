from health_records_db import load_records


def get_patient_history(nhid):

    db = load_records()

    history = []

    for r in db:
        if r["nhid"] == nhid:
            history.append(r)

    return history
