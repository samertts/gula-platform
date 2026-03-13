import datetime
import json

LOG_FILE = "system_logs.json"


def log_event(event):

    data = {"time": str(datetime.datetime.now()), "event": event}

    try:
        with open(LOG_FILE) as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append(data)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def analyze_logs():

    try:
        with open(LOG_FILE) as f:
            logs = json.load(f)
    except:
        return "No logs"

    errors = [l for l in logs if "error" in l["event"].lower()]

    if len(errors) > 5:
        return "⚠ High error rate detected"

    return "System healthy"
