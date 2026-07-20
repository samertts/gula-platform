"""AI-powered fraud detection for national health insurance.

Detection capabilities:
  - Duplicate claims
  - Repeated laboratory tests
  - Fake referrals
  - Provider abuse patterns
  - Patient abuse patterns
  - Suspicious billing
  - Service inflation
  - Ghost patients
  - Identity abuse
  - Unusual ordering patterns
"""

from __future__ import annotations

from app.insurance.fraud.detector import FraudDetectionEngine, FraudRule, FraudSignal

__all__ = ["FraudDetectionEngine", "FraudRule", "FraudSignal"]
