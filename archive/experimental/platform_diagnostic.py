import os
import socket
import requests
import subprocess
import sys

print("---- Lab Platform Diagnostic Tool ----\n")

# فحص Python
print("Python Version:", sys.version)

# فحص الملفات الأساسية
required_files = [
    "core/api/main.py",
    "device_simulator.py",
]

print("\nChecking project files...")
for f in required_files:
    if os.path.exists(f):
        print("OK:", f)
    else:
        print("MISSING:", f)

# فحص المنفذ 8000
print("\nChecking port 8000...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("localhost", 8000))
if result == 0:
    print("Port 8000 is open")
else:
    print("Port 8000 is CLOSED")

# اختبار API
print("\nTesting API...")
try:
    r = requests.get("http://localhost:8000")
    print("API Response:", r.status_code)
except:
    print("API not reachable")

# فحص المكتبات
print("\nChecking installed packages...")
try:
    import fastapi
    print("FastAPI OK")
except:
    print("FastAPI MISSING")

try:
    import pydantic
    print("Pydantic OK")
except:
    print("Pydantic MISSING")

print("\nDiagnostic Complete")
