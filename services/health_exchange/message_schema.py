def create_lab_result_message(nhid, test, value, date):

    message = {
        "type": "lab_result",
        "nhid": nhid,
        "test": test,
        "value": value,
        "date": date,
    }

    return message
