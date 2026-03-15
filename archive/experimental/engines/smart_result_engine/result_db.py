import json
import os

DB = os.path.expanduser("~/lab-platform/database/results.json")


def load_results():

    if not os.path.exists(DB):
        return []

    with open(DB) as f:
        return json.load(f)


def save_results(data):

    with open(DB, "w") as f:
        json.dump(data, f, indent=2)
