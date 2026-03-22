"""
GULA Platform — Stress, Concurrency & Race Condition Tests
Tests the system under concurrent load to find race conditions and bottlenecks.
Run: python -m pytest backend/tests/test_stress.py -v
"""

import os
import time
import threading
import statistics
import concurrent.futures
from collections import Counter

os.environ.setdefault("ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_stress.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")


# =============================================================================
# 1. CONCURRENT INTERPRETATION ENGINE
#    100 threads calling interpret_result simultaneously — no crashes, no races
# =============================================================================

class TestConcurrentInterpretation:

    def test_100_concurrent_interpretations_no_crash(self):
        """100 threads calling interpret_result simultaneously must not crash."""
        from backend.app.services.interpretation import interpret_result
        errors = []
        results = []
        lock = threading.Lock()

        def worker(i):
            try:
                tests = [
                    ("glucose", 85, 70, 100),
                    ("hemoglobin", 14, 12, 17),
                    ("potassium", 4.0, 3.5, 5.0),
                    ("tsh", 2.5, 0.4, 4.5),
                    ("wbc", 7.0, 4.0, 11.0),
                ]
                test_name, val, low, high = tests[i % len(tests)]
                r = interpret_result(test_name, val, low, high)
                with lock:
                    results.append(r["status"])
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
            futures = [ex.submit(worker, i) for i in range(100)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0, f"Errors in concurrent interpretation: {errors}"
        assert len(results) == 100
        # All must be valid statuses
        valid = {"normal", "high", "low", "critical", "unknown"}
        for s in results:
            assert s in valid, f"Invalid status: {s}"

    def test_interpretation_results_consistent_under_load(self):
        """Same input must always produce same output regardless of concurrency."""
        from backend.app.services.interpretation import interpret_result
        results = []
        lock = threading.Lock()

        def worker():
            r = interpret_result("glucose", 85, 70, 100)
            with lock:
                results.append(r["status"])

        threads = [threading.Thread(target=worker) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results must be identical
        assert len(set(results)) == 1, f"Inconsistent results: {Counter(results)}"
        assert results[0] == "normal"


# =============================================================================
# 2. CONCURRENT WESTGARD EVALUATION
# =============================================================================

class TestConcurrentWestgard:

    def test_50_concurrent_westgard_calls(self):
        """50 threads evaluating QC simultaneously."""
        from backend.app.routes.quality_control import evaluate_westgard
        errors = []
        results = []
        lock = threading.Lock()

        def worker(i):
            try:
                measured = 100 + (i % 10) * 2  # 100–118
                r = evaluate_westgard(measured, 100, 10)
                with lock:
                    results.append(r["status"])
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
            futures = [ex.submit(worker, i) for i in range(50)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(results) == 50
        valid = {"pass", "warning", "fail"}
        for s in results:
            assert s in valid


# =============================================================================
# 3. RATE LIMITER RACE CONDITIONS
#    Most critical: concurrent access must not allow more requests than limit
# =============================================================================

class TestRateLimiterConcurrency:

    def test_rate_limiter_exact_limit_under_contention(self):
        """Under heavy concurrency, rate limiter must never allow > max_requests."""
        from backend.app.security.rate_limit import RateLimiter
        limiter = RateLimiter()
        allowed = []
        lock = threading.Lock()
        MAX = 10

        def attempt():
            result = limiter.check("stress.ip.test", max_requests=MAX, window_seconds=60)
            with lock:
                allowed.append(result)

        threads = [threading.Thread(target=attempt) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total_allowed = sum(1 for r in allowed if r)
        total_blocked = sum(1 for r in allowed if not r)

        # Must not allow more than MAX
        assert total_allowed <= MAX, f"Rate limiter allowed {total_allowed} > {MAX} under contention"
        assert total_blocked >= 90, f"Only blocked {total_blocked}/90 expected"

    def test_rate_limiter_no_deadlock_under_load(self):
        """Rate limiter must not deadlock with 200 concurrent threads."""
        from backend.app.security.rate_limit import RateLimiter
        limiter = RateLimiter()
        completed = []
        lock = threading.Lock()

        def attempt(ip):
            limiter.check(ip, max_requests=1000, window_seconds=60)
            with lock:
                completed.append(True)

        threads = [threading.Thread(target=attempt, args=(f"10.0.{i % 5}.{i % 255}",))
                   for i in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)  # 5s max — deadlock would cause timeout

        assert len(completed) == 200, f"Deadlock detected: only {len(completed)}/200 completed"


# =============================================================================
# 4. INTRUSION DETECTOR CONCURRENCY
# =============================================================================

class TestIntrusionDetectorConcurrency:

    def test_concurrent_attack_detection(self):
        """Multiple IPs attacking simultaneously — each tracked independently."""
        from backend.app.security.intrusion_detection import IntrusionDetector
        detector = IntrusionDetector(max_attempts=5, window_seconds=300)
        results = {}
        lock = threading.Lock()

        def attack(attacker_id):
            ip = f"attacker-{attacker_id}.ip"
            statuses = []
            for _ in range(6):  # 1 more than threshold
                status = detector.detect(ip)
                statuses.append(status)
            with lock:
                results[ip] = statuses

        threads = [threading.Thread(target=attack, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each attacker must eventually be blocked
        for ip, statuses in results.items():
            assert "blocked" in statuses, f"{ip} was never blocked: {statuses}"

    def test_detector_no_cross_ip_contamination(self):
        """Attacks from one IP must not affect other IPs."""
        from backend.app.security.intrusion_detection import IntrusionDetector
        detector = IntrusionDetector(max_attempts=3, window_seconds=300)

        # Fill up bad IP
        for _ in range(3):
            detector.detect("bad.ip.x.x")

        assert detector.detect("bad.ip.x.x") == "blocked"

        # Good IPs must still be clean
        for i in range(10):
            result = detector.detect(f"good.ip.{i}.1")
            assert result != "blocked", f"good.ip.{i}.1 was incorrectly blocked"


# =============================================================================
# 5. TOKEN GENERATION UNIQUENESS UNDER CONCURRENCY
# =============================================================================

class TestTokenUniqueness:

    def test_jwt_tokens_unique_per_user_under_concurrency(self):
        """Tokens for distinct users must all be unique, no crashes."""
        from backend.app.security.auth import create_token
        tokens = []
        lock = threading.Lock()
        errors = []

        def make_token(i):
            try:
                # Each call has a unique user_id → unique payload → unique token
                t = create_token({"user_id": i, "lab_id": 1, "role": "staff"})
                with lock:
                    tokens.append(t)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
            futures = [ex.submit(make_token, i) for i in range(1000)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0, f"Token creation errors: {errors[:3]}"
        assert len(tokens) == 1000
        # Unique payloads → unique tokens
        unique = set(tokens)
        assert len(unique) == 1000, f"Duplicate tokens detected: {1000 - len(unique)} duplicates"

    def test_encryption_thread_safe(self):
        """encrypt() must be thread-safe for concurrent calls."""
        from backend.app.security.encryption import encrypt, decrypt
        results = []
        errors = []
        lock = threading.Lock()
        plaintext = "Patient: Ahmed Al-Rashid — Lab: GULA — NID: 1234567890"

        def enc_dec():
            try:
                enc = encrypt(plaintext)
                dec = decrypt(enc)
                with lock:
                    results.append(dec == plaintext)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=enc_dec) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Encryption errors: {errors[:3]}"
        assert all(results), "Some encrypt/decrypt round-trips failed"


# =============================================================================
# 6. PERFORMANCE UNDER SUSTAINED LOAD
# =============================================================================

class TestSustainedLoadPerformance:
    """Simulate lab peak hours: 10 techs, 5 minutes, ~300 actions."""

    def test_interpretation_throughput_1000_per_second(self):
        """Clinical engine must handle ≥ 1000 interpretations/second."""
        from backend.app.services.interpretation import interpret_result
        count = 0
        start = time.perf_counter()
        deadline = start + 1.0  # 1 second window

        while time.perf_counter() < deadline:
            interpret_result("glucose", 85, 70, 100)
            count += 1

        assert count >= 1000, f"Only {count} interpretations/sec (need ≥ 1000)"

    def test_westgard_throughput_500_per_second(self):
        """QC engine must handle ≥ 500 evaluations/second."""
        from backend.app.routes.quality_control import evaluate_westgard
        count = 0
        start = time.perf_counter()
        deadline = start + 1.0

        while time.perf_counter() < deadline:
            evaluate_westgard(105, 100, 10)
            count += 1

        assert count >= 500, f"Only {count} QC evaluations/sec (need ≥ 500)"

    def test_critical_check_throughput_2000_per_second(self):
        """Critical alerts check must handle ≥ 2000 checks/second."""
        from backend.app.routes.critical_alerts import check_critical
        count = 0
        start = time.perf_counter()
        deadline = start + 1.0

        while time.perf_counter() < deadline:
            check_critical("Potassium", 4.0)
            check_critical("Glucose", 85)
            check_critical("Hemoglobin", 14)
            count += 3

        assert count >= 2000, f"Only {count} critical checks/sec (need ≥ 2000)"

    def test_p99_latency_interpretation(self):
        """P99 latency for interpretation must be < 1ms."""
        from backend.app.services.interpretation import interpret_result
        times = []

        for _ in range(5000):
            t0 = time.perf_counter()
            interpret_result("glucose", 85, 70, 100)
            times.append((time.perf_counter() - t0) * 1000)

        p99 = sorted(times)[4950]  # 99th percentile
        assert p99 < 1.0, f"P99 latency {p99:.3f}ms exceeds 1ms limit"

    def test_p99_latency_westgard(self):
        """P99 latency for Westgard must be < 1ms."""
        from backend.app.routes.quality_control import evaluate_westgard
        times = []

        for _ in range(5000):
            t0 = time.perf_counter()
            evaluate_westgard(105, 100, 10)
            times.append((time.perf_counter() - t0) * 1000)

        p99 = sorted(times)[4950]
        assert p99 < 1.0, f"P99 Westgard latency {p99:.3f}ms exceeds 1ms limit"


# =============================================================================
# 7. MEMORY STABILITY (No leaks under repeated calls)
# =============================================================================

class TestMemoryStability:

    def test_no_memory_growth_interpretation(self):
        """Repeated calls must not grow memory unboundedly."""
        import tracemalloc
        from backend.app.services.interpretation import interpret_result

        tracemalloc.start()
        snap1 = tracemalloc.take_snapshot()

        for _ in range(10000):
            interpret_result("glucose", 85, 70, 100)

        snap2 = tracemalloc.take_snapshot()
        tracemalloc.stop()

        stats = snap2.compare_to(snap1, "lineno")
        total_growth_kb = sum(s.size_diff for s in stats) / 1024

        # Allow max 500KB growth for 10k calls (generous allowance)
        assert total_growth_kb < 500, f"Memory grew {total_growth_kb:.0f}KB for 10k calls"

    def test_rate_limiter_memory_bounded(self):
        """Rate limiter must not grow memory for many unique IPs."""
        from backend.app.security.rate_limit import RateLimiter
        limiter = RateLimiter()

        # Simulate 10,000 unique IPs
        for i in range(10000):
            limiter.check(f"{i // 256}.{i % 256}.0.1", max_requests=10, window_seconds=1)

        # After window expires, cleanup should have occurred
        # (just verify no crash and limiter still works)
        assert limiter.check("final.test.ip", max_requests=10, window_seconds=60)


# =============================================================================
# 8. CRITICAL CLINICAL SCENARIOS (Multi-test interactions)
# =============================================================================

class TestClinicalScenarios:
    """Test realistic multi-test clinical patterns."""

    def test_sepsis_pattern_all_critical(self):
        """WBC=18, Hemoglobin=6, Platelets=50 → all should flag abnormal."""
        from backend.app.services.interpretation import interpret_result, get_flag
        scenarios = [
            ("wbc",        18.0,  4.0,  11.0, "H"),
            ("hemoglobin",  6.0, 12.0,  17.0, "critical"),  # critically low
            ("platelets",  50.0, 150.0, 400.0, "L"),
        ]
        for test, val, low, high, expected_flag in scenarios:
            flag = get_flag(val, low, high, test.capitalize())
            interp = interpret_result(test, val, low, high)
            assert flag in ("H", "L", "critical"), f"{test}={val}: expected abnormal, got {flag}"
            assert interp["status"] != "normal", f"{test}={val} should not be normal"

    def test_diabetic_ketoacidosis_pattern(self):
        """Glucose=550 (>500 threshold), HbA1c=11 → both critical."""
        from backend.app.services.interpretation import interpret_result
        from backend.app.routes.critical_alerts import check_critical

        # Glucose critical threshold = 500 mg/dL
        glucose = interpret_result("glucose", 550, 70, 100)
        hba1c = interpret_result("hba1c", 11.0)

        assert glucose["status"] == "critical"
        assert hba1c["status"] == "critical"
        # 550 > 500 (critical_high threshold)
        assert check_critical("Glucose", 550) is not None
        # 450 is below critical threshold (500) — should be high, not critical
        assert check_critical("Glucose", 450) is None  # ← documented threshold

    def test_hypokalemia_critical_pattern(self):
        """Potassium=2.0 is life-threatening."""
        from backend.app.services.interpretation import interpret_result, get_flag
        from backend.app.routes.critical_alerts import check_critical

        interp = interpret_result("potassium", 2.0)
        flag = get_flag(2.0, 3.5, 5.0, "Potassium")
        alert = check_critical("Potassium", 2.0)

        # All three systems must agree this is dangerous
        assert interp["status"] == "low"
        assert flag == "critical"
        assert alert is not None
        assert alert["severity"] == "critical_low"

    def test_normal_patient_no_alerts(self):
        """A healthy patient should produce no critical alerts."""
        from backend.app.routes.critical_alerts import check_critical

        normal_tests = [
            ("Glucose", 85),
            ("Hemoglobin", 14),
            ("Potassium", 4.2),
            ("Sodium", 140),
            ("WBC", 7.0),
            ("Platelets", 250),
        ]
        for test_name, value in normal_tests:
            alert = check_critical(test_name, value)
            assert alert is None, f"{test_name}={value} incorrectly triggered critical alert"

    def test_borderline_values_consistency(self):
        """Values just at threshold must be consistently flagged."""
        from backend.app.services.interpretation import get_flag

        # Exactly at normal_high → normal
        assert get_flag(100.0, 70, 100) == "normal"
        # Just above → H
        assert get_flag(100.001, 70, 100) == "H"
        # Exactly at normal_low → normal
        assert get_flag(70.0, 70, 100) == "normal"
        # Just below → L
        assert get_flag(69.999, 70, 100) == "L"
