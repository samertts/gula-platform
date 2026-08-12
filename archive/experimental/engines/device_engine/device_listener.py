import socket

from drivers import *
from drivers.registry import detect_device
from result_storage import save_results

HOST = "0.0.0.0"
PORT = 5000


def start_listener():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print("Global Device Engine Started")

    while True:

        conn, addr = server.accept()

        print("Device connected:", addr)

        data = conn.recv(4096).decode()

        if "GET" in data:
            conn.send(b"HTTP/1.1 200 OK\n\nDevice Engine Running")
            conn.close()
            continue

        print("Raw data:", data)

        driver = detect_device(data)

        if driver is None:

            print("Unknown device")
            conn.close()
            continue

        print("Detected device:", driver.name)

        parsed = driver.parse(data)

        save_results(
            device=driver.name, patient_id="auto_patient", parsed_results=parsed
        )

        print("Stored results:", parsed)

        conn.close()


if __name__ == "__main__":
    start_listener()
