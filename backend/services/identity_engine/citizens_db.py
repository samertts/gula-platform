import json
import uuid

DB_FILE = "citizens.json"


def load_db():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except:
        return []


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_nhid():
    return "NH-" + str(uuid.uuid4())[:8]
