#!/bin/bash

echo "Starting core services..."

uvicorn services.patient_service.main:app --port 8001 &
uvicorn services.lab_service.main:app --port 8002 &
uvicorn services.order_service.main:app --port 8003 &
uvicorn services.result_service.main:app --port 8004 &
uvicorn services.sample_service.main:app --port 8005 &
uvicorn services.notification_service.main:app --port 8006 &
uvicorn services.identity_service.main:app --port 8007 &

echo "All services started"
