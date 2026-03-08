import datetime
import json

LOG = "autonomous_actions.json"


def log_action(action, details):

    entry = {"time": str(datetime.datetime.now()), "action": action, "details": details}

    try:
        with open(LOG) as f:
            data = json.load(f)
    except:
        data = []

    data.append(entry)

    with open(LOG, "w") as f:
        json.dump(data, f, indent=2)
