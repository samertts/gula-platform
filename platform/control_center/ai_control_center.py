import os
import time
import psutil
import subprocess
from datetime import datetime

BASE = os.path.expanduser("~/lab-platform")

SERVICES = {
    "API": "api/main.py",
    "Identity Engine": "identity_engine/citizen_registry.py",
    "Health Record Engine": "health_record_engine/record_manager.py",
    "Result Engine": "smart_result_engine/result_entry.py",
    "Network Orchestrator": "network_orchestrator/orchestrator_engine.py",
    "National Intelligence": "national_intelligence/intelligence_dashboard.py"
}

REPORT = os.path.join(BASE, "system_health_report.txt")

def check_cpu():
    return psutil.cpu_percent(interval=1)

def check_memory():
    return psutil.virtual_memory().percent

def check_disk():
    return psutil.disk_usage("/").percent

def service_running(name):
    for p in psutil.process_iter(["cmdline"]):
        try:
            cmd = " ".join(p.info["cmdline"])
            if name in cmd:
                return True
        except:
            pass
    return False

def restart_service(script):
    path = os.path.join(BASE, script)
    if os.path.exists(path):
        subprocess.Popen(["python3", path])

def check_services():

    status = {}

    for name, script in SERVICES.items():

        running = service_running(script)

        if not running:
            restart_service(script)

        status[name] = "RUNNING" if running else "RESTARTED"

    return status

def generate_report():

    cpu = check_cpu()
    memory = check_memory()
    disk = check_disk()
    services = check_services()

    report = []
    report.append(f"System report {datetime.now()}")
    report.append("----------------------------------")

    report.append(f"CPU usage: {cpu}%")
    report.append(f"Memory usage: {memory}%")
    report.append(f"Disk usage: {disk}%")

    report.append("\nServices:")

    for s in services:
        report.append(f"{s}: {services[s]}")

    with open(REPORT, "w") as f:
        f.write("\n".join(report))

    print("\n".join(report))

def monitor():

    while True:

        generate_report()

        time.sleep(300)

if __name__ == "__main__":
    monitor()
