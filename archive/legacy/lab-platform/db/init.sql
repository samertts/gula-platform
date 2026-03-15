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
