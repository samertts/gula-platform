from lab_registry import load_labs


def check_lab_status():

    labs = load_labs()

    report = []

    for lab in labs:

        if lab["status"] == "online":
            state = "OK"
        else:
            state = "DOWN"

        report.append({"lab": lab["name"], "status": state})

    return report
