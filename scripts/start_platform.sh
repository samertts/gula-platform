#!/bin/bash

echo "Starting Lab Platform..."

# تحديث المسار
export PYTHONPATH=$PYTHONPATH:$(pwd)

# إنشاء بيئة افتراضية إذا لم توجد
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# تفعيل البيئة
source venv/bin/activate

# تثبيت المكتبات
pip install --upgrade pip
pip install fastapi uvicorn psycopg2-binary requests

# تشغيل قاعدة بيانات بسيطة SQLite إذا لم توجد PostgreSQL
echo "Preparing database..."

# تشغيل API
echo "Starting API server..."
uvicorn core.api.main:app --host 0.0.0.0 --port 8000 &

API_PID=$!

sleep 3

# تشغيل لوحة التحكم
echo "Starting dashboard..."
python3 intelligence_dashboard.py &

DASH_PID=$!

echo "--------------------------------"
echo "Lab Platform Running"
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "--------------------------------"

wait $API_PID
wait $DASH_PID
