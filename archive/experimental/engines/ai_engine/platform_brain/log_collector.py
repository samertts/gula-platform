import datetime
import json

LOG_FILE = "platform_logs.json"


def log_event(service, message, level="INFO"):

    entry = {
        "time": str(datetime.datetime.now()),
        "service": service,
        "level": level,
        "message": message,
    }

    try:
        with open(LOG_FILE) as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def read_logs():
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except:
        return []
