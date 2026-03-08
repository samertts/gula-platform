import json
import os

RECORD_DB = os.path.expanduser(
    "~/lab-platform/health_record_engine/health_records.json"
)


def load_health_data():
    try:
        with open(RECORD_DB) as f:
            return json.load(f)
    except:
        return []
