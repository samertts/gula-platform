def create_lab_result_message(nhid, test, value, date):

    return {
        "type": "lab_result",
        "nhid": nhid,
        "test": test,
        "value": value,
        "date": date,
    }

