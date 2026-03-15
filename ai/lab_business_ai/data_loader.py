import json
import os

DB = os.path.expanduser("~/gula-platform/health_record_engine/health_records.json")


def load_data():

    try:
        with open(DB) as f:
            return json.load(f)
    except:
        return []
