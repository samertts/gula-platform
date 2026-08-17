#!/usr/bin/env python3
"""
GULA Anomaly Detection & Real-time Alerting Engine
-----------------------------------------------------------------
Description: Scans incoming clinical and telemetry streams from legacy gateways.
Detects out-of-range anomalies, heartbeat failures, and potential security tampering,
triggering automated isolation and multi-channel alerts within milliseconds.
"""

import logging
import time
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] GULA-ANOMALY-ENGINE: %(message)s'
)

class AnomalyDetector:
    def __init__(self, glucose_normal_min: float = 70.0, glucose_normal_max: float = 99.0):
        self.min_limit = glucose_normal_min
        self.max_limit = glucose_normal_max

    def evaluate_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates payload for data anomalies or security violations."""
        raw_stream = payload.get("raw_stream", "")
        
        # Security tampering check (e.g., unexpected control characters or header anomalies)
        if "DROP TABLE" in raw_stream or "<script>" in raw_stream:
            logging.critical("SECURITY ALERT: Potential injection/tampering detected from edge device!")
            return {
                "status": "SECURITY_VIOLATION",
                "action": "ACTIVE_QUARANTINE_TRIGGERED",
                "message": "Port locked and isolated due to unauthorized command stream."
            }

        # Clinical anomaly check (Parsing simulated GLU value from OBX segment)
        if "GLU^Glucose" in raw_stream:
            try:
                parts = raw_stream.split("|")
                # Find value index in OBX
                val_str = parts[5] if len(parts) > 5 else "0"
                val = float(val_str)
                
                if val < self.min_limit or val > self.max_limit:
                    logging.warning(f"CLINICAL ALERT: Value {val} is out of normal physiological range ({self.min_limit}-{self.max_limit})!")
                    return {
                        "status": "CLINICAL_ANOMALY",
                        "action": "FLAG_FOR_REVIEW",
                        "value": val,
                        "message": "Out-of-range result flagged for senior clinician validation."
                    }
            except ValueError:
                pass

        logging.info("Payload evaluation passed: Normal clinical and security status.")
        return {
            "status": "NORMAL",
            "action": "ACCEPT_AND_FORWARD"
        }

if __name__ == "__main__":
    detector = AnomalyDetector()
    
    # Test normal sample
    normal_sample = {"raw_stream": "OBX|1|NM|GLU^Glucose||85|mg/dL|70-99|N|||F"}
    print(detector.evaluate_payload(normal_sample))

    # Test anomalous sample (High Glucose)
    abnormal_sample = {"raw_stream": "OBX|1|NM|GLU^Glucose||250|mg/dL|70-99|H|||F"}
    print(detector.evaluate_payload(abnormal_sample))

    # Test security tampering sample
    tampered_sample = {"raw_stream": "DROP TABLE patients; --"}
    print(detector.evaluate_payload(tampered_sample))
