
CREATE TABLE IF NOT EXISTS roles (

id SERIAL PRIMARY KEY,
name TEXT UNIQUE

);

CREATE TABLE IF NOT EXISTS permissions (

id SERIAL PRIMARY KEY,
name TEXT UNIQUE

);

CREATE TABLE IF NOT EXISTS role_permissions (

role_id INTEGER,
permission_id INTEGER

);

CREATE TABLE IF NOT EXISTS user_roles (

user_id INTEGER,
role_id INTEGER

);


INSERT INTO roles (name) VALUES
('super_admin'),
('ministry_admin'),
('governorate_admin'),
('lab_owner'),
('lab_manager'),
('lab_validator'),
('lab_technician'),
('doctor'),
('nurse'),
('patient'),
('device'),
('api_client'),
('ai_agent'),
('auditor')
ON CONFLICT DO NOTHING;


INSERT INTO permissions (name) VALUES
('view_dashboard'),
('view_patients'),
('create_patient'),
('view_results'),
('validate_results'),
('view_labs'),
('manage_labs'),
('manage_users'),
('manage_devices'),
('view_analytics'),
('manage_billing'),
('system_admin')
ON CONFLICT DO NOTHING;

