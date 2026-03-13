import json

DB_FILE = "health_records.json"


def load_records():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except:
        return []


def save_records(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)
