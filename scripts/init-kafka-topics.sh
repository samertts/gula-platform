#!/bin/bash
# =============================================================================
# GULA Platform - Kafka Topics Initialization
# Executive Order 18: Data pipeline topics
# =============================================================================

set -euo pipefail

KAFKA_HOST="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"

echo "Waiting for Kafka to be ready..."
until kafka-topics --bootstrap-server "${KAFKA_HOST}" --list > /dev/null 2>&1; do
    echo "Kafka not ready, waiting..."
    sleep 5
done

echo "Creating GULA Kafka topics..."

topics=(
    "gula.lab-results:3:1"
    "gula.alerts:1:1"
    "gula.audit:1:1"
    "gula.analytics:3:1"
    "gula.outbreak-detection:1:1"
    "gula.notifications:2:1"
)

for topic_config in "${topics[@]}"; do
    IFS=: read -r topic partitions replication <<< "${topic_config}"
    kafka-topics --bootstrap-server "${KAFKA_HOST}" \
        --create --if-not-exists \
        --topic "${topic}" \
        --partitions "${partitions}" \
        --replication-factor "${replication}" \
        --config retention.ms=604800000
    echo "Created topic: ${topic}"
done

echo "All Kafka topics created."
kafka-topics --bootstrap-server "${KAFKA_HOST}" --list
