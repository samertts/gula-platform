"""
GULA Platform — Lab Simulation Load Test
Simulates a real lab with ~150–300 tests/hour

Usage:
  pip install locust
  locust -f tests/load/locustfile.py --host http://localhost:8000
  locust -f tests/load/locustfile.py --host http://localhost:8000 --users 50 --spawn-rate 5 --headless --run-time 2m

Scenarios:
  - LabTechnicianUser: enters results fast (heavy writer)
  - DoctorReviewUser:  views results (reader)
  - AdminDashboard:    monitors stats (low frequency)
"""

import random
import time
from locust import HttpUser, task, between, tag, events


# ─── Shared state (set by login) ─────────────────────────────────────────────
_tokens = {}   # username → token


# ─── Credentials (dev defaults) ──────────────────────────────────────────────
LAB_CREDENTIALS = {"username": "admin", "password": "admin123"}

# Sample clinical data for realistic test entry
SAMPLE_TESTS = [
    {"test_name": "Hemoglobin",  "unit": "g/dL",       "normal_range_low": 12.0,  "normal_range_high": 17.0},
    {"test_name": "WBC",         "unit": "x10^3/uL",   "normal_range_low": 4.0,   "normal_range_high": 11.0},
    {"test_name": "Platelets",   "unit": "x10^3/uL",   "normal_range_low": 150.0, "normal_range_high": 400.0},
    {"test_name": "Glucose",     "unit": "mg/dL",       "normal_range_low": 70.0,  "normal_range_high": 100.0},
    {"test_name": "Creatinine",  "unit": "mg/dL",       "normal_range_low": 0.6,   "normal_range_high": 1.3},
    {"test_name": "ALT",         "unit": "U/L",         "normal_range_low": 0.0,   "normal_range_high": 40.0},
    {"test_name": "TSH",         "unit": "mIU/L",       "normal_range_low": 0.4,   "normal_range_high": 4.5},
    {"test_name": "Cholesterol", "unit": "mg/dL",       "normal_range_low": 0.0,   "normal_range_high": 200.0},
    {"test_name": "Potassium",   "unit": "mEq/L",       "normal_range_low": 3.5,   "normal_range_high": 5.0},
    {"test_name": "Sodium",      "unit": "mEq/L",       "normal_range_low": 135.0, "normal_range_high": 145.0},
]

PATIENT_NAMES = [
    "Ahmed Al-Rashid", "Sara Mohammed", "Ali Hassan", "Fatima Al-Zahra",
    "Omar Khalid", "Nour Ibrahim", "Youssef Karim", "Layla Ahmad",
]


def _random_value(test):
    """Generate a realistic value (80% normal, 15% abnormal, 5% critical)."""
    roll = random.random()
    low, high = test["normal_range_low"], test["normal_range_high"]
    if roll < 0.80:
        # Normal
        return round(random.uniform(low, high), 2)
    elif roll < 0.95:
        # Abnormal (outside range)
        if random.random() < 0.5:
            return round(random.uniform(low * 0.3, low * 0.95), 2)
        else:
            return round(random.uniform(high * 1.05, high * 1.8), 2)
    else:
        # Critical
        if test["test_name"] == "Potassium":
            return round(random.uniform(6.5, 8.0), 2)
        elif test["test_name"] == "Hemoglobin":
            return round(random.uniform(3.0, 5.0), 2)
        else:
            return round(high * 3.5, 2)


# =============================================================================
# USER TYPE 1: Lab Technician (heavy writer — 60% of load)
# =============================================================================

class LabTechnicianUser(HttpUser):
    """
    Simulates a lab technician entering results throughout the day.
    ~150 tests/hour → 1 every 24s per technician.
    """
    weight = 60
    wait_time = between(15, 45)  # 15–45s between actions (realistic pace)

    def on_start(self):
        """Login once and cache token."""
        self.token = self._login()
        self.patient_ids = []

    def _login(self):
        with self.client.post(
            "/login",
            json=LAB_CREDENTIALS,
            catch_response=True,
            name="[auth] login",
        ) as r:
            if r.status_code == 200:
                data = r.json()
                token = data.get("access_token") or data.get("token", "")
                r.success()
                return token
            else:
                r.failure(f"Login failed: {r.status_code}")
                return ""

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    @tag("write", "critical-path")
    def enter_result_order(self):
        """Core task: create a new patient + order + results (full workflow)."""
        # Step 1: Create patient
        patient_name = random.choice(PATIENT_NAMES)
        with self.client.post(
            "/patients",
            json={
                "full_name": patient_name,
                "gender": random.choice(["male", "female"]),
                "birth_date": "1985-06-15",
                "phone": f"07{random.randint(700000000, 799999999)}",
            },
            headers=self._headers(),
            catch_response=True,
            name="[result] create patient",
        ) as r:
            if r.status_code not in (200, 201):
                r.failure(f"Create patient failed: {r.status_code}")
                return
            patient_id = r.json().get("id")
            if not patient_id:
                r.failure("No patient ID in response")
                return
            r.success()

        # Step 2: Enter results (2–5 tests per order, realistic)
        n_tests = random.randint(2, 5)
        selected = random.sample(SAMPLE_TESTS, n_tests)
        results = [
            {
                "test_name": t["test_name"],
                "value": _random_value(t),
                "unit": t["unit"],
                "normal_range_low": t["normal_range_low"],
                "normal_range_high": t["normal_range_high"],
            }
            for t in selected
        ]

        with self.client.post(
            "/results/order",
            json={
                "patient_id": patient_id,
                "doctor_name": "Dr. Ali Hassan",
                "results": results,
            },
            headers=self._headers(),
            catch_response=True,
            name="[result] enter order",
        ) as r:
            if r.status_code not in (200, 201):
                r.failure(f"Enter results failed: {r.status_code}")
                return
            r.success()

    @task(3)
    @tag("read")
    def view_patient_results(self):
        """View recent results (common during verification)."""
        with self.client.get(
            "/results?page=1&page_size=10",
            headers=self._headers(),
            catch_response=True,
            name="[result] view recent",
        ) as r:
            if r.status_code not in (200, 401, 403):
                r.failure(f"View results: {r.status_code}")
            else:
                r.success()

    @task(2)
    @tag("read")
    def view_samples_queue(self):
        """Check pending samples queue."""
        with self.client.get(
            "/samples?status=pending&page_size=20",
            headers=self._headers(),
            catch_response=True,
            name="[sample] queue",
        ) as r:
            if r.status_code not in (200, 401, 403):
                r.failure(f"Sample queue: {r.status_code}")
            else:
                r.success()


# =============================================================================
# USER TYPE 2: Doctor / Reviewer (reader — 30% of load)
# =============================================================================

class DoctorReviewUser(HttpUser):
    """
    Simulates a doctor reviewing results.
    Mostly reads, occasional searches.
    """
    weight = 30
    wait_time = between(30, 90)

    def on_start(self):
        self.token = self._login()

    def _login(self):
        with self.client.post(
            "/login",
            json=LAB_CREDENTIALS,
            catch_response=True,
            name="[auth] login",
        ) as r:
            if r.status_code == 200:
                token = r.json().get("access_token") or r.json().get("token", "")
                r.success()
                return token
            r.failure(f"Login: {r.status_code}")
            return ""

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    @tag("read", "doctor")
    def view_critical_alerts(self):
        """Doctors check critical alerts frequently."""
        with self.client.get(
            "/alerts?hours=24",
            headers=self._headers(),
            catch_response=True,
            name="[alert] critical list",
        ) as r:
            if r.status_code not in (200, 401, 403):
                r.failure(f"Critical alerts: {r.status_code}")
            else:
                r.success()

    @task(3)
    @tag("read", "doctor")
    def search_patient(self):
        """Search for a patient by name."""
        name = random.choice(["Ahmed", "Sara", "Ali", "Omar"])
        with self.client.get(
            f"/patients?search={name}&page_size=10",
            headers=self._headers(),
            catch_response=True,
            name="[patient] search",
        ) as r:
            if r.status_code not in (200, 401, 403):
                r.failure(f"Patient search: {r.status_code}")
            else:
                r.success()

    @task(2)
    @tag("read", "doctor")
    def view_dashboard(self):
        """Dashboard stats."""
        with self.client.get(
            "/dashboard",
            headers=self._headers(),
            catch_response=True,
            name="[dashboard] stats",
        ) as r:
            if r.status_code not in (200, 401, 403):
                r.failure(f"Dashboard: {r.status_code}")
            else:
                r.success()


# =============================================================================
# USER TYPE 3: Admin Monitor (low frequency — 10% of load)
# =============================================================================

class AdminDashboardUser(HttpUser):
    """
    Lab admin checking system status and QC.
    Low frequency, important paths.
    """
    weight = 10
    wait_time = between(60, 180)

    def on_start(self):
        self.token = self._login()

    def _login(self):
        with self.client.post(
            "/login",
            json=LAB_CREDENTIALS,
            catch_response=True,
            name="[auth] login",
        ) as r:
            if r.status_code == 200:
                token = r.json().get("access_token") or r.json().get("token", "")
                r.success()
                return token
            r.failure(f"Login: {r.status_code}")
            return ""

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    @tag("admin")
    def view_qc_status(self):
        """Quality control status check."""
        with self.client.get(
            "/qc?page_size=20",
            headers=self._headers(),
            catch_response=True,
            name="[qc] status",
        ) as r:
            if r.status_code not in (200, 401, 403):
                r.failure(f"QC status: {r.status_code}")
            else:
                r.success()

    @task(2)
    @tag("admin")
    def health_check(self):
        """System health (also tests infra)."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="[system] health",
        ) as r:
            if r.status_code != 200:
                r.failure(f"Health check: {r.status_code}")
            elif r.json().get("status") != "healthy":
                r.failure(f"Unhealthy: {r.json()}")
            else:
                r.success()

    @task(1)
    @tag("admin")
    def alert_stats(self):
        """Critical alert statistics."""
        with self.client.get(
            "/alerts/stats",
            headers=self._headers(),
            catch_response=True,
            name="[alert] stats",
        ) as r:
            if r.status_code not in (200, 401, 403):
                r.failure(f"Alert stats: {r.status_code}")
            else:
                r.success()


# =============================================================================
# PERFORMANCE THRESHOLDS (exit with failure if violated)
# =============================================================================

@events.quitting.add_listener
def check_thresholds(environment, **kwargs):
    """Fail the load test if SLAs are violated."""
    stats = environment.stats

    failures = []

    # Max acceptable failure rate: 1%
    total = stats.total
    if total.num_requests > 0:
        failure_rate = total.num_failures / total.num_requests * 100
        if failure_rate > 1.0:
            failures.append(f"Failure rate {failure_rate:.1f}% exceeds 1%")

    # P95 latency must be < 2000ms
    if total.get_response_time_percentile(0.95) > 2000:
        p95 = total.get_response_time_percentile(0.95)
        failures.append(f"P95 latency {p95:.0f}ms exceeds 2000ms SLA")

    if failures:
        print("\n❌ SLA VIOLATIONS:")
        for f in failures:
            print(f"  - {f}")
        environment.process_exit_code = 1
    else:
        print("\n✅ All SLAs passed")
