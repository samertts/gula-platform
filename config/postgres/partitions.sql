-- =============================================================================
-- GULA PLATFORM - Partition Management Function
-- Executive Order 11: Auto-create monthly partitions
-- =============================================================================

-- Function to auto-create next month's partition
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, year INT, month INT)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date     DATE;
    end_date       DATE;
BEGIN
    partition_name := table_name || '_' || year || '_' || LPAD(month::TEXT, 2, '0');
    start_date     := DATE(year || '-' || LPAD(month::TEXT, 2, '0') || '-01');
    end_date       := start_date + INTERVAL '1 month';

    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
            partition_name, table_name, start_date, end_date
        );
        RAISE NOTICE 'Created partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to ensure next 3 months always have partitions
CREATE OR REPLACE FUNCTION ensure_future_partitions()
RETURNS VOID AS $$
DECLARE
    future_month DATE;
    y INT;
    m INT;
BEGIN
    FOR i IN 0..3 LOOP
        future_month := DATE_TRUNC('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
        y := EXTRACT(YEAR FROM future_month)::INT;
        m := EXTRACT(MONTH FROM future_month)::INT;
        PERFORM create_monthly_partition('test_results', y, m);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Run immediately to ensure current partitions exist
SELECT ensure_future_partitions();

-- =============================================================================
-- pg_hba.conf for replication
-- =============================================================================
-- (This is handled by the pg_hba.conf file mount in docker-compose)
