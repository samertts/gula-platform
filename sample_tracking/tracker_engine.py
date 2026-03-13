import time
from datetime import datetime

SAMPLES = {}

ALERT_TIME = 600  # 10 دقائق بدون حركة

def register_sample(sample_id, patient, test):

    SAMPLES[sample_id] = {
        "patient": patient,
        "test": test,
        "unit": "Reception",
        "device": None,
        "operator": None,
        "status": "Received",
        "last_move": time.time(),
        "history": []
    }

    log(sample_id, "Sample registered")

def move_sample(sample_id, unit, device, operator):

    if sample_id not in SAMPLES:
        return

    SAMPLES[sample_id]["unit"] = unit
    SAMPLES[sample_id]["device"] = device
    SAMPLES[sample_id]["operator"] = operator
    SAMPLES[sample_id]["status"] = "Processing"
    SAMPLES[sample_id]["last_move"] = time.time()

    log(sample_id, f"Moved to {unit} / {device}")

def complete_sample(sample_id):

    if sample_id not in SAMPLES:
        return

    SAMPLES[sample_id]["status"] = "Completed"
    SAMPLES[sample_id]["last_move"] = time.time()

    log(sample_id, "Analysis completed")

def log(sample_id, message):

    SAMPLES[sample_id]["history"].append({
        "time": str(datetime.now()),
        "event": message
    })

def detect_lost_samples():

    now = time.time()

    alerts = []

    for s in SAMPLES:

        if now - SAMPLES[s]["last_move"] > ALERT_TIME:

            alerts.append(s)

    return alerts
