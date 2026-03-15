import json
import os

DB = os.path.expanduser("~/lab-platform/health_record_engine/health_records.json")


def load_records():
    try:
        with open(DB) as f:
            return json.load(f)
    except:
        return []
