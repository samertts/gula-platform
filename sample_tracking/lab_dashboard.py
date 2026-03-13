from tracker_engine import SAMPLES

def show_dashboard():

    print("======== LAB SAMPLE BOARD ========")

    for s in SAMPLES:

        data = SAMPLES[s]

        print("--------------------------------")

        print("Sample:", s)
        print("Patient:", data["patient"])
        print("Test:", data["test"])
        print("Unit:", data["unit"])
        print("Device:", data["device"])
        print("Operator:", data["operator"])
        print("Status:", data["status"])
