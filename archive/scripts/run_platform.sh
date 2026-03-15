
#!/bin/bash
echo "Starting Lab Platform Services..."

uvicorn services.patient_service.main:app --port 8001 &
uvicorn services.lab_service.main:app --port 8002 &
uvicorn services.order_service.main:app --port 8003 &
uvicorn services.result_service.main:app --port 8004 &
uvicorn services.sample_service.main:app --port 8005 &
uvicorn services.notification_service.main:app --port 8006 &
uvicorn services.identity_service.main:app --port 8007 &
uvicorn gateway.api_gateway:app --port 8000 &

echo "All services started"
