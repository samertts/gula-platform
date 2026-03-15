#!/bin/bash

echo "Creating project..."

mkdir lab-platform
cd lab-platform

mkdir api db frontend

touch api/main.py
touch db/init.sql
touch requirements.txt

echo "Writing requirements..."

cat <<EOF > requirements.txt
fastapi
uvicorn
psycopg2-binary
sqlalchemy
pydantic
EOF

echo "Writing database schema..."

cat <<EOF > db/init.sql
CREATE TABLE patients (
id SERIAL PRIMARY KEY,
name VARCHAR(200),
phone VARCHAR(50)
);

CREATE TABLE orders (
id SERIAL PRIMARY KEY,
patient_id INTEGER,
status VARCHAR(50)
);

CREATE TABLE results (
id SERIAL PRIMARY KEY,
order_id INTEGER,
test_name VARCHAR(100),
value FLOAT
);
EOF

echo "Writing API..."

cat <<EOF > api/main.py
from fastapi import FastAPI
import psycopg2

app = FastAPI()

conn = psycopg2.connect(
    host="localhost",
    database="labdb",
    user="postgres",
    password="postgres"
)

@app.get("/")
def home():
    return {"message":"Lab Platform Running"}

@app.post("/patients")
def create_patient(name:str,phone:str):

    cur=conn.cursor()

    cur.execute(
        "INSERT INTO patients(name,phone) VALUES(%s,%s)",
        (name,phone)
    )

    conn.commit()

    return {"status":"patient created"}

@app.get("/patients")
def list_patients():

    cur=conn.cursor()

    cur.execute("SELECT * FROM patients")

    return cur.fetchall()

@app.post("/orders")
def create_order(patient_id:int):

    cur=conn.cursor()

    cur.execute(
        "INSERT INTO orders(patient_id,status) VALUES(%s,'created')",
        (patient_id,)
    )

    conn.commit()

    return {"status":"order created"}

@app.post("/results")
def add_result(order_id:int,test_name:str,value:float):

    cur=conn.cursor()

    cur.execute(
        "INSERT INTO results(order_id,test_name,value) VALUES(%s,%s,%s)",
        (order_id,test_name,value)
    )

    conn.commit()

    return {"status":"result stored"}
EOF

echo "Installing packages..."

pip install -r requirements.txt

echo "Starting server..."
uvicorn api.main:app --reload
