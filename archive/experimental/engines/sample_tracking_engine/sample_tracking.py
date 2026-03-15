
import time

samples = {}

def update_sample(sample_id, location, device, technician):

    samples[sample_id] = {
        "location": location,
        "device": device,
        "technician": technician
    }

def monitor():

    while True:

        for s in samples:
            print("Sample:", s, samples[s])

        time.sleep(5)

if __name__ == "__main__":
    monitor()
