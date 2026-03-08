#!/bin/bash

echo "Starting Lab Platform installation..."

mkdir lab-platform
cd lab-platform

echo "Creating folders..."

mkdir api
mkdir ai
mkdir device_engine
mkdir workflow_engine
mkdir db
mkdir frontend

touch api/main.py
touch requirements.txt
touch db/schema.sql
touch frontend/index.html

echo "Writing requirements..."

cat <<EOF > requirements.txt
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pydantic
python-barcode
reportlab
EOF

echo "Writing database schema..."

cat <<EOF > db/schema.sql
CREATE TABLE patients (
id SERIAL PRIMARY KEY,
name VARCHAR(200),
phone VARCHAR(50),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
id SERIAL PRIMARY KEY,
patient_id INTEGER,
status VARCHAR(50),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE samples (
id SERIAL PRIMARY KEY,
sample_code VARCHAR(50),
order_id INTEGER,
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

app = FastAPI()

@app.get("/")
def home():
return {"message":"Lab Platform Started"}

@app.get("/health")
def health():
return {"status":"ok"}
EOF

echo "Installing Python libraries..."

pip install -r requirements.txt

echo "Project structure created."

echo "To start server run:"

echo "uvicorn api.main:app --reload"
