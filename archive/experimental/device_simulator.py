import requests
import random
import time

API_URL = "http://localhost:8000/results"

tests = [
    ("WBC", "10^3/uL", 4, 11),
    ("RBC", "10^6/uL", 4.5, 6),
    ("HGB", "g/dL", 12, 18),
    ("PLT", "10^3/uL", 150, 400),
]

def generate_result():
    test = random.choice(tests)
    value = round(random.uniform(test[2], test[3]), 2)

    return {
        "sample_id": random.randint(1000, 9999),
        "test_code": test[0],
        "result": value,
        "unit": test[1]
    }

while True:
    data = generate_result()

    try:
        r = requests.post(API_URL, json=data)
        print("Sent:", data, "Status:", r.status_code)
    except:
        print("API not reachable")

    time.sleep(5)
