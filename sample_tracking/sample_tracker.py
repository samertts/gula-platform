import time
from datetime import datetime

samples = {}

def register_sample(sample_id, patient, test):

    samples[sample_id] = {
        "patient": patient,
        "test": test,
        "unit": "Reception",
        "device": None,
        "operator": None,
        "status": "Received",
        "time_remaining": None,
        "history": []
    }

    log(sample_id, "Sample received")

def move_sample(sample_id, unit, device, operator, minutes):

    if sample_id not in samples:
        return "Sample not found"

    samples[sample_id]["unit"] = unit
    samples[sample_id]["device"] = device
    samples[sample_id]["operator"] = operator
    samples[sample_id]["status"] = "Processing"
    samples[sample_id]["time_remaining"] = minutes

    log(sample_id, f"Moved to {unit} / {device}")

def complete_sample(sample_id):

    if sample_id not in samples:
        return

    samples[sample_id]["status"] = "Completed"
    samples[sample_id]["time_remaining"] = 0

    log(sample_id, "Analysis completed")

def log(sample_id, message):

    samples[sample_id]["history"].append({
        "time": str(datetime.now()),
        "event": message
    })

def get_sample_status(sample_id):

    return samples.get(sample_id, "Sample not found")

def show_all_samples():

    for s in samples:

        data = samples[s]

        print("--------------------------------")

        print("Sample:", s)
        print("Patient:", data["patient"])
        print("Test:", data["test"])
        print("Unit:", data["unit"])
        print("Device:", data["device"])
        print("Operator:", data["operator"])
        print("Status:", data["status"])
        print("Remaining:", data["time_remaining"])

# مثال تشغيل

if __name__ == "__main__":

    register_sample("S1001", "Ali Hassan", "CBC")

    move_sample("S1001", "Hematology Unit", "Analyzer 3", "Ahmed", 3)

    time.sleep(1)

    show_all_samples()
