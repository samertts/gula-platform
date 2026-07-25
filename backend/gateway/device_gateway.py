import os
import socket

import requests

HOST = "0.0.0.0"
PORT = 5000

API_URL = os.getenv("LAB_API_URL", "http://lab-api:8000/results")
API_TOKEN = os.getenv("LAB_DEVICE_TOKEN", "devicesecret")


def parse_message(msg: str):
    """
    مثال بسيط لتحليل رسالة قادمة من جهاز.
    يمكن استبداله بـ HL7 أو ASTM parser لاحقًا.
    الرسالة المتوقعة:
    order_id|test_id|value
    """

    parts = msg.strip().split("|")

    if len(parts) != 3:
        return None

    return {"order_id": int(parts[0]), "test_id": int(parts[1]), "value": parts[2]}


def send_result(data):

    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    r = requests.post(API_URL, params=data, headers=headers)

    return r.status_code


def run_server():

    s = socket.socket()
    s.bind((HOST, PORT))
    s.listen(5)

    while True:
        conn, _addr = s.accept()

        data = conn.recv(1024).decode()

        parsed = parse_message(data)

        if parsed:
            send_result(parsed)

        conn.close()


if __name__ == "__main__":
    run_server()
