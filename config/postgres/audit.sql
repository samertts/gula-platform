-- =============================================================================
-- GULA PLATFORM - Medical Audit Log
-- Executive Order 5: Mandatory audit for all medical operations
-- =============================================================================

-- =============================================================================
-- AUDIT LOG TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    event_id        UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    event_type      TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       BIGINT,
    entity_uuid     UUID,
    actor_id        BIGINT,
    actor_username  TEXT,
    actor_role      TEXT,
    lab_id          BIGINT,
    ip_address      TEXT,
    user_agent      TEXT,
    old_values      JSONB,
    new_values      JSONB,
    metadata        JSONB,
    severity        TEXT DEFAULT 'info' CHECK (severity IN ('debug','info','warning','critical')),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast queries
CREATE INDEX idx_audit_log_event_type  ON audit_log(event_type);
CREATE INDEX idx_audit_log_entity      ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_actor       ON audit_log(actor_id);
CREATE INDEX idx_audit_log_lab_id      ON audit_log(lab_id);
CREATE INDEX idx_audit_log_created_at  ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_severity    ON audit_log(severity, created_at DESC);

-- =============================================================================
-- MANDATORY AUDIT EVENTS (Executive Order 5)
-- PatientCreated, SampleCollected, ResultUpdated, ResultValidated, OrderCompleted
-- =============================================================================

-- Audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_event TEXT;
    old_json JSONB;
    new_json JSONB;
BEGIN
    IF TG_OP = 'INSERT' THEN
        audit_event := TG_TABLE_NAME || '.created';
        old_json := NULL;
        new_json := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        audit_event := TG_TABLE_NAME || '.updated';
        old_json := to_jsonb(OLD);
        new_json := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        audit_event := TG_TABLE_NAME || '.deleted';
        old_json := to_jsonb(OLD);
        new_json := NULL;
    END IF;

    INSERT INTO audit_log (
        event_type,
        entity_type,
        entity_id,
        old_values,
        new_values,
        severity
    ) VALUES (
        audit_event,
        TG_TABLE_NAME,
        CASE WHEN TG_OP = 'DELETE' THEN (old_json->>'id')::BIGINT
             ELSE (new_json->>'id')::BIGINT END,
        old_json,
        new_json,
        'info'
    );

    IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to critical tables
CREATE TRIGGER patients_audit
    AFTER INSERT OR UPDATE OR DELETE ON patients
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER test_orders_audit
    AFTER INSERT OR UPDATE OR DELETE ON test_orders
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER test_results_audit
    AFTER INSERT OR UPDATE OR DELETE ON test_results
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER samples_audit
    AFTER INSERT OR UPDATE OR DELETE ON samples
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER users_audit
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- =============================================================================
-- CIRCUIT BREAKER STATE TABLE (Executive Order 7)
-- =============================================================================
CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    id              BIGSERIAL PRIMARY KEY,
    service_name    TEXT UNIQUE NOT NULL,
    state           TEXT DEFAULT 'closed' CHECK (state IN ('closed','open','half-open')),
    failure_count   INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP,
    opened_at       TIMESTAMP,
    next_retry_at   TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO circuit_breaker_state (service_name, state) VALUES
('lab-service', 'closed'),
('patient-service', 'closed'),
('order-service', 'closed'),
('result-service', 'closed'),
('sample-service', 'closed'),
('notification-service', 'closed'),
('ai-service', 'closed'),
('ollama', 'closed')
ON CONFLICT DO NOTHING;
