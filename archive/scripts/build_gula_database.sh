#!/bin/bash

BASE=~/gula-platform
DB=$BASE/database

mkdir -p $DB

echo "Building GULA Database..."

########################################
echo "Creating schema.sql"
########################################

cat > $DB/schema.sql <<'EOF'

CREATE TABLE IF NOT EXISTS users (

id SERIAL PRIMARY KEY,
username TEXT UNIQUE,
password TEXT,
role TEXT,
created_at TIMESTAMP DEFAULT now()

);

CREATE TABLE IF NOT EXISTS labs (

id SERIAL PRIMARY KEY,
name TEXT,
city TEXT,
capacity INTEGER,
created_at TIMESTAMP DEFAULT now()

);

CREATE TABLE IF NOT EXISTS patients (

id SERIAL PRIMARY KEY,
name TEXT,
national_id TEXT,
gender TEXT,
birth_date DATE,
created_at TIMESTAMP DEFAULT now()

);

CREATE TABLE IF NOT EXISTS orders (

id SERIAL PRIMARY KEY,
patient_id INTEGER,
lab_id INTEGER,
status TEXT,
created_at TIMESTAMP DEFAULT now()

);

CREATE TABLE IF NOT EXISTS samples (

id SERIAL PRIMARY KEY,
sample_code TEXT,
order_id INTEGER,
status TEXT,
created_at TIMESTAMP DEFAULT now()

);

CREATE TABLE IF NOT EXISTS tests (

id SERIAL PRIMARY KEY,
name TEXT,
category TEXT,
normal_min FLOAT,
normal_max FLOAT

);

CREATE TABLE IF NOT EXISTS results (

id SERIAL PRIMARY KEY,
order_id INTEGER,
test_id INTEGER,
value FLOAT,
status TEXT,
created_at TIMESTAMP DEFAULT now()

);

CREATE TABLE IF NOT EXISTS devices (

id SERIAL PRIMARY KEY,
name TEXT,
model TEXT,
lab_id INTEGER

);

CREATE TABLE IF NOT EXISTS subscriptions (

id SERIAL PRIMARY KEY,
lab_id INTEGER,
plan TEXT,
price FLOAT,
start_date DATE,
end_date DATE

);

CREATE TABLE IF NOT EXISTS payments (

id SERIAL PRIMARY KEY,
lab_id INTEGER,
amount FLOAT,
method TEXT,
status TEXT,
created_at TIMESTAMP DEFAULT now()

);

CREATE TABLE IF NOT EXISTS audit_logs (

id SERIAL PRIMARY KEY,
user_id INTEGER,
action TEXT,
created_at TIMESTAMP DEFAULT now()

);

EOF

########################################
echo "Applying schema to PostgreSQL"
########################################

docker exec -i postgres-primary psql -U postgres -d postgres < $DB/schema.sql

echo "Database created successfully"
