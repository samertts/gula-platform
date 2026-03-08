import datetime

from health_records_db import load_records, save_records


def add_test_result(nhid, test, value):

    db = load_records()

    record = {
        "nhid": nhid,
        "test": test,
        "value": value,
        "date": str(datetime.date.today()),
    }

    db.append(record)

    save_records(db)

    return record
