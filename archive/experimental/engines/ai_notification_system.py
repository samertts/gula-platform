import sqlite3
import requests
import time

DB = "/home/samertts/lab-platform/db/lab.db"

TELEGRAM_TOKEN = "BOT_TOKEN"
TELEGRAM_CHAT = "CHAT_ID"

SMS_API = "https://sms-api.example/send"

CRITICAL_LIMITS = {
    "glucose": 400,
    "potassium": 6,
    "hemoglobin": 5
}

def send_telegram(msg):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT,
        "text": msg
    })

def send_sms(phone, msg):

    requests.post(SMS_API, json={
        "phone": phone,
        "message": msg
    })

def analyze_result(test, value):

    if test in CRITICAL_LIMITS:

        if float(value) > CRITICAL_LIMITS[test]:

            return "critical"

    return "normal"

def notify_doctor(result):

    msg = f"""
CRITICAL LAB RESULT

Patient: {result['patient']}
Test: {result['test']}
Value: {result['value']}
"""

    send_telegram(msg)

def notify_patient(result):

    msg = f"""
Your lab result is ready

Test: {result['test']}
Value: {result['value']}
"""

    send_sms(result["phone"], msg)

def check_results():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT id,patient,test,value,phone,doctor_phone
    FROM results
    WHERE notified=0
    """).fetchall()

    for r in rows:

        result = {
            "id": r[0],
            "patient": r[1],
            "test": r[2],
            "value": r[3],
            "phone": r[4],
            "doctor_phone": r[5]
        }

        status = analyze_result(result["test"], result["value"])

        notify_patient(result)

        if status == "critical":

            notify_doctor(result)

        cur.execute(
            "UPDATE results SET notified=1 WHERE id=?",
            (result["id"],)
        )

    conn.commit()
    conn.close()

def check_devices():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT name,status
    FROM devices
    WHERE status='offline'
    """).fetchall()

    for d in rows:

        msg = f"Device failure detected: {d[0]}"

        send_telegram(msg)

    conn.close()

def monitor():

    print("AI Notification System started")

    while True:

        check_results()
        check_devices()

        time.sleep(30)

if __name__ == "__main__":

    monitor()
