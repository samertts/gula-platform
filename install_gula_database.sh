#!/bin/bash

echo "Installing GULA database schema..."

DB="gula"

########################################
# create database
########################################

sudo -u postgres psql <<EOF

CREATE DATABASE $DB;

EOF

########################################
# install extensions
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

EOF

########################################
# HEALTH IDENTITY
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE health_identity (

patient_uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

national_id_encrypted BYTEA,

national_id_hash TEXT UNIQUE,

insurance_id TEXT,

health_card_number TEXT,

national_id_verified BOOLEAN DEFAULT false,

national_registry_linked BOOLEAN DEFAULT false,

biometric_hash TEXT,

face_hash TEXT,

nfc_signature BYTEA,

created_at TIMESTAMPTZ DEFAULT now(),

updated_at TIMESTAMPTZ DEFAULT now()

);

EOF

########################################
# PATIENT DEMOGRAPHICS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE patient_demographics (

patient_uuid UUID PRIMARY KEY REFERENCES health_identity(patient_uuid),

full_name_ar TEXT NOT NULL,

full_name_en TEXT,

mother_name_ar TEXT,

mother_name_en TEXT,

birth_date DATE NOT NULL,

birth_place TEXT,

family_id TEXT,

blood_type TEXT,

gender CHAR(1),

address TEXT,

phone_numbers TEXT[],

emails TEXT[],

created_at TIMESTAMPTZ DEFAULT now()

);

EOF

########################################
# PATIENT INSURANCE
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE patient_insurance (

id SERIAL PRIMARY KEY,

patient_uuid UUID REFERENCES health_identity(patient_uuid),

insurance_id TEXT NOT NULL,

provider TEXT,

start_date DATE,

end_date DATE,

is_active BOOLEAN DEFAULT true

);

EOF

########################################
# IDENTITY HISTORY
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE identity_history (

id SERIAL PRIMARY KEY,

patient_uuid UUID REFERENCES health_identity(patient_uuid),

changed_field TEXT,

old_value TEXT,

new_value TEXT,

changed_at TIMESTAMPTZ DEFAULT now(),

changed_by UUID

);

EOF

########################################
# LEGAL CONSENTS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE legal_consents (

id SERIAL PRIMARY KEY,

patient_uuid UUID REFERENCES health_identity(patient_uuid),

consent_type TEXT,

version TEXT,

granted BOOLEAN,

granted_at TIMESTAMPTZ,

ip_address INET,

user_agent TEXT

);

EOF

########################################
# MEDICAL EVENTS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE medical_events (

event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

patient_uuid UUID REFERENCES health_identity(patient_uuid),

event_type TEXT,

event_date TIMESTAMPTZ,

description TEXT,

created_by UUID,

created_at TIMESTAMPTZ DEFAULT now()

);

EOF

########################################
# LAB ORDERS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE lab_orders (

order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

patient_uuid UUID REFERENCES health_identity(patient_uuid),

ordered_by UUID,

order_date TIMESTAMPTZ,

status TEXT,

notes TEXT

);

EOF

########################################
# LAB RESULTS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE lab_results (

result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

order_id UUID REFERENCES lab_orders(order_id),

test_name TEXT,

value TEXT,

unit TEXT,

reference_range TEXT,

status TEXT,

result_date TIMESTAMPTZ

);

EOF

########################################
# PRESCRIPTIONS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE prescriptions (

prescription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

patient_uuid UUID REFERENCES health_identity(patient_uuid),

doctor_uuid UUID,

prescription_date TIMESTAMPTZ,

notes TEXT

);

EOF

########################################
# MEDICATIONS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE medications (

id SERIAL PRIMARY KEY,

prescription_id UUID REFERENCES prescriptions(prescription_id),

drug_name TEXT,

dose TEXT,

duration TEXT

);

EOF

########################################
# VACCINATIONS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE vaccinations (

vaccination_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

patient_uuid UUID REFERENCES health_identity(patient_uuid),

vaccine_name TEXT,

dose_number INT,

vaccination_date DATE,

provider TEXT

);

EOF

########################################
# CHRONIC DISEASES
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE chronic_diseases (

id SERIAL PRIMARY KEY,

patient_uuid UUID REFERENCES health_identity(patient_uuid),

disease_name TEXT,

diagnosis_date DATE,

doctor_uuid UUID

);

EOF

########################################
# NOTIFICATIONS
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE notifications (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

patient_uuid UUID REFERENCES health_identity(patient_uuid),

channel TEXT,

message TEXT,

sent_at TIMESTAMPTZ DEFAULT now(),

status TEXT

);

EOF

########################################
# AUDIT LOG
########################################

sudo -u postgres psql -d $DB <<EOF

CREATE TABLE audit_log (

id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

patient_uuid UUID,

actor_uuid UUID,

action_type TEXT,

resource_type TEXT,

resource_id UUID,

old_values JSONB,

new_values JSONB,

timestamp TIMESTAMPTZ DEFAULT now(),

ip_address INET,

device_fingerprint TEXT

);

EOF

echo "GULA database installed successfully."
