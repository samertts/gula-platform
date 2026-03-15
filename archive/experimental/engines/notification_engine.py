import smtplib
import sqlite3
import time
from email.mime.text import MIMEText

DB = "/home/samertts/lab-platform/db/lab.db"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "lab.notifications@gmail.com"
SMTP_PASS = "app_password"

def send_email(to, subject, body):

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to

    s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    s.starttls()
    s.login(SMTP_USER, SMTP_PASS)
    s.send_message(msg)
    s.quit()

def notify_patient(result):

    body = f"""
    Dear patient,

    Your lab test result is ready.

    Test: {result['test']}
    Value: {result['value']}

    Please consult your doctor.

    """

    send_email(result["patient_email"], "Lab Result Ready", body)

def notify_doctor(result):

    body = f"""
    Patient result requires review.

    Patient: {result['patient_name']}
    Test: {result['test']}
    Value: {result['value']}

    """

    send_email(result["doctor_email"], "Patient Lab Result", body)

def notify_missing_sample(sample):

    body = f"""
    ALERT

    Sample lost

    Sample ID: {sample['id']}
    Last location: {sample['location']}
    """

    send_email(sample["lab_admin_email"], "Sample Lost Alert", body)

def notify_device_failure(device):

    body = f"""
    Device failure detected

    Device: {device['name']}
    Status: {device['status']}
    """

    send_email(device["admin_email"], "Device Failure", body)

def check_results():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT id,test,value,patient_email,doctor_email,patient_name,notified FROM results WHERE notified=0"
    ).fetchall()

    for r in rows:

        result = {
            "id": r[0],
            "test": r[1],
            "value": r[2],
            "patient_email": r[3],
            "doctor_email": r[4],
            "patient_name": r[5],
        }

        notify_patient(result)
        notify_doctor(result)

        cur.execute("UPDATE results SET notified=1 WHERE id=?", (r[0],))

    conn.commit()
    conn.close()

def check_devices():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT name,status,admin_email FROM devices WHERE status='offline'"
    ).fetchall()

    for r in rows:

        device = {"name": r[0], "status": r[1], "admin_email": r[2]}

        notify_device_failure(device)

    conn.close()

def check_samples():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT id,location,admin_email FROM samples WHERE lost=1"
    ).fetchall()

    for r in rows:

        sample = {"id": r[0], "location": r[1], "lab_admin_email": r[2]}

        notify_missing_sample(sample)

    conn.close()

def run():

    print("Notification engine started")

    while True:

        check_results()
        check_devices()
        check_samples()

        time.sleep(60)

if __name__ == "__main__":
    run()
