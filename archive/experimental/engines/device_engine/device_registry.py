import json

FILE = "devices.json"


def save_devices(devices):

    with open(FILE, "w") as f:
        json.dump(devices, f, indent=4)


def load_devices():

    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return []
