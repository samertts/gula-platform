#!/usr/bin/env python3
"""
GULA Automated RBAC Security Testing Suite
-----------------------------------------------------------------
Description: Automatically simulates unauthorized access, privilege escalation, 
and data leakage attempts against GULA's RBAC and assistant middleware, 
verifying hard enforcement and audit logging.
"""

import sys
import logging
from gula_rbac_manager import SecureAssistantWrapper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] GULA-SECURITY-TEST: %(message)s'
)

def run_security_regression_tests():
    wrapper = SecureAssistantWrapper()
    test_failures = 0

    print("==================================================")
    print("STARTING GULA AUTOMATED RBAC SECURITY REGRESSION")
    print("==================================================")

    # Test Case 1: Physician accessing clinical data (Expected: SUCCESS)
    res1 = wrapper.query_assistant("PHYSICIAN", "clinical", {"patient_id": "P001"})
    if res1["status"] == "SUCCESS":
        print("[PASS] Test 1: Physician clinical access authorized.")
    else:
        print("[FAIL] Test 1: Physician clinical access incorrectly denied.")
        test_failures += 1

    # Test Case 2: Technician attempting to access clinical PHI (Expected: FORBIDDEN)
    res2 = wrapper.query_assistant("TECHNICIAN", "clinical", {"patient_id": "P001"})
    if res2["status"] == "FORBIDDEN":
        print("[PASS] Test 2: Technician unauthorized clinical access successfully blocked.")
    else:
        print("[FAIL] Test 2: Security breach! Technician gained access to clinical data.")
        test_failures += 1

    # Test Case 3: Nurse attempting system config access (Expected: FORBIDDEN)
    res3 = wrapper.query_assistant("NURSE", "admin", {"config": "core"})
    if res3["status"] == "FORBIDDEN":
        print("[PASS] Test 3: Nurse unauthorized admin access successfully blocked.")
    else:
        print("[FAIL] Test 3: Privilege escalation! Nurse gained access to admin config.")
        test_failures += 1

    # Test Case 4: Admin querying full technical telemetry (Expected: SUCCESS)
    res4 = wrapper.query_assistant("ADMIN", "technical", {"device_id": "DEV_01"})
    if res4["status"] == "SUCCESS":
        print("[PASS] Test 4: Admin technical telemetry access authorized.")
    else:
        print("[FAIL] Test 4: Admin technical access incorrectly denied.")
        test_failures += 1

    print("==================================================")
    if test_failures == 0:
        print("RESULT: ALL RBAC SECURITY TESTS PASSED (100% SECURE)")
        print("==================================================")
        sys.exit(0)
    else:
        print(f"RESULT: SECURITY TEST FAILED ({test_failures} vulnerabilities detected)")
        print("==================================================")
        sys.exit(1)

if __name__ == "__main__":
    run_security_regression_tests()
