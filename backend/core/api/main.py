import os
import sys
from datetime import UTC, datetime, timedelta

import psycopg2
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from joserfc import jwk
from joserfc import jwt as jose_jwt
from passlib.hash import bcrypt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = FastAPI(title="National Laboratory Platform")

# Load configuration from environment variables - fail fast if missing
DB_HOST = os.getenv("DB_HOST", "")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASS = os.getenv("DB_PASS", "")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASS]):
    sys.exit(1)

AI_SERVICE = os.getenv("AI_SERVICE_URL", "http://ai-service:9000")

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    sys.exit(1)

ALGORITHM = "HS256"


def db():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)


@app.get("/")
def root():
    return {"system": "National Lab Platform Running"}


# --------------------
# USERS
# --------------------


@app.post("/register")
def register(username: str, password: str):

    hashed = bcrypt.hash(password)

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users(username,password)
        VALUES(%s,%s)
        RETURNING id
        """,
        (username, hashed),
    )

    uid = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"user_id": uid}


@app.post("/login")
def login(username: str, password: str):

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT id,password FROM users WHERE username=%s", (username,))

    row = cur.fetchone()

    if not row:
        raise HTTPException(401, "Invalid credentials")

    uid, hashed = row

    if not bcrypt.verify(password, hashed):
        raise HTTPException(401, "Invalid credentials")

    token = jose_jwt.encode(
        {"alg": ALGORITHM},
        {"user_id": uid, "exp": datetime.now(UTC) + timedelta(hours=12)},
        jwk.OctKey.import_key(SECRET_KEY),
    )

    return {"token": token}


# --------------------
# PATIENTS
# --------------------


@app.post("/patients")
def create_patient(first_name: str, last_name: str, age: int, gender: str):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO patients(first_name,last_name,age,gender)
        VALUES(%s,%s,%s,%s)
        RETURNING id
        """,
        (first_name, last_name, age, gender),
    )

    pid = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"patient_id": pid}


@app.get("/patients")
def list_patients():

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM patients")

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


# --------------------
# TESTS
# --------------------


@app.get("/tests")
def list_tests():

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM lab_tests")

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


# --------------------
# ORDERS
# --------------------


@app.post("/orders")
def create_order(patient_id: int):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO test_orders(patient_id)
        VALUES(%s)
        RETURNING id
        """,
        (patient_id,),
    )

    oid = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"order_id": oid}


# --------------------
# RESULTS
# --------------------


@app.post("/results")
def add_result(order_id: int, test_id: int, value: str):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO test_results(order_id,test_id,result_value)
        VALUES(%s,%s,%s)
        RETURNING id
        """,
        (order_id, test_id, value),
    )

    rid = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"result_id": rid}


# --------------------
# PDF REPORT
# --------------------


@app.get("/report/{result_id}")
def generate_report(result_id: int):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT p.first_name, p.last_name, t.test_name, r.result_value
        FROM test_results r
        JOIN test_orders o ON r.order_id = o.id
        JOIN patients p ON o.patient_id = p.id
        JOIN lab_tests t ON r.test_id = t.id
        WHERE r.id = %s
    """,
        (result_id,),
    )

    row = cur.fetchone()

    if not row:
        raise HTTPException(404, "Result not found")

    first, last, test, value = row

    filename = f"/tmp/report_{result_id}.pdf"

    c = canvas.Canvas(filename, pagesize=letter)

    c.drawString(100, 700, "Laboratory Report")
    c.drawString(100, 650, f"Patient: {first} {last}")
    c.drawString(100, 620, f"Test: {test}")
    c.drawString(100, 590, f"Result: {value}")

    c.save()

    cur.close()
    conn.close()

    return FileResponse(filename, filename="lab_report.pdf")


# --------------------
# AI CBC ANALYSIS
# --------------------


@app.post("/cbc/analyze")
def analyze_cbc(hb: float, wbc: float, platelets: float):

    ai = requests.post(
        f"{AI_SERVICE}/analyze-cbc",
        params={"hb": hb, "wbc": wbc, "platelets": platelets},
    )

    return ai.json()


# --------------------
# QUALITY CONTROL
# --------------------


@app.post("/qc")
def add_qc(test_id: int, value: float):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO quality_control(test_id,qc_value)
        VALUES(%s,%s)
        RETURNING id
        """,
        (test_id, value),
    )

    qid = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"qc_id": qid}


@app.get("/qc")
def list_qc():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT qc.id, t.test_name, qc.qc_value, qc.qc_date
        FROM quality_control qc
        JOIN lab_tests t ON qc.test_id = t.id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


@app.post("/qc/analyze")
def analyze_qc(test_id: int, value: float):

    ai = requests.post(
        f"{AI_SERVICE}/agent",
        params={
            "task": f"""
Analyze laboratory quality control value.

Test ID: {test_id}
QC Value: {value}

Determine if the value indicates instrument drift or normal variation.
"""
        },
    )

    return ai.json()


# --------------------
# ANALYTICS
# --------------------


@app.get("/analytics/tests-per-day")
def tests_per_day():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DATE(created_at), COUNT(*)
        FROM test_results
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


@app.get("/analytics/top-tests")
def top_tests():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.test_name, COUNT(*)
        FROM test_results r
        JOIN lab_tests t ON r.test_id = t.id
        GROUP BY t.test_name
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


@app.get("/analytics/abnormal-rate")
def abnormal_rate():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
        COUNT(*) FILTER (WHERE result_value ~ '[^0-9.]') AS abnormal,
        COUNT(*) AS total
        FROM test_results
    """)

    row = cur.fetchone()

    cur.close()
    conn.close()

    abnormal, total = row

    if total == 0:
        return {"rate": 0}

    rate = (abnormal / total) * 100

    return {"abnormal_rate_percent": rate}
