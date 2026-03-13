import json

DB = "labs.json"


def load_labs():
    try:
        with open(DB) as f:
            return json.load(f)
    except:
        return []


def save_labs(data):
    with open(DB, "w") as f:
        json.dump(data, f, indent=2)


def register_lab(name, city, capacity):

    labs = load_labs()

    lab = {"name": name, "city": city, "capacity": capacity, "status": "online"}

    labs.append(lab)

    save_labs(labs)

    return lab
