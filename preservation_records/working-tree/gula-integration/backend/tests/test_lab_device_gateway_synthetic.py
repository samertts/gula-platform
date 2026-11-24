"""Phase D (F-070 / D-023) — Lab Device Gateway, synthetic messages only.

No real analyzer, no network, no operational DB. All samples/devices/values are
fictional. Covers device identity, input validation, HMAC, replay window,
nonce replay, and the fail-closed fix when the nonce store is unavailable.

Evidence id: E-056 (see GOVERNANCE/GECS/EVIDENCE_REGISTRY.md).
"""

from __future__ import annotations

import time

import pytest

from app.gateways import lab_device_gateway as gw
from app.gateways.lab_device_gateway import DeviceAuthError, DeviceInputError


class _FakeCache:
    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value


class _BrokenCache:
    def get(self, key):
        raise RuntimeError("synthetic Redis outage")

    def set(self, key, value, ex=None):
        raise RuntimeError("synthetic Redis outage")


@pytest.fixture
def open_gateway(monkeypatch):
    """No HMAC key configured (dev/test mode) — validation still applies."""
    monkeypatch.setattr(gw, "_DEVICE_HMAC_KEY", "")
    monkeypatch.setattr(gw, "_ALLOWED_DEVICE_IDS", set())
    return gw


@pytest.fixture
def secure_gateway(monkeypatch):
    """HMAC + whitelist + replay protection configured; fake nonce store."""
    monkeypatch.setattr(gw, "_DEVICE_HMAC_KEY", "synthetic-hmac-key")
    monkeypatch.setattr(gw, "_ALLOWED_DEVICE_IDS", {"analyzer-01"})
    cache = _FakeCache()
    monkeypatch.setattr("app.security.redis_client.cache", cache)
    return gw, cache


def _signed(*, value="13.0", device="analyzer-01", sample="SAMPLE-1",
            test="glucose", nonce="nonce-1", timestamp=None, key="synthetic-hmac-key"):
    ts = timestamp if timestamp is not None else int(time.time())
    signature = gw._compute_signature(device, sample, test, float(value), ts)
    return dict(
        sample_id=sample, test=test, value=value, device_id=device,
        signature=signature, timestamp=ts, nonce=nonce,
    )


class TestInputValidation:
    def test_happy_path_unconfigured_key(self, open_gateway):
        result = gw.receive_device_result("SAMPLE-1", "glucose", "13.0", device_id="analyzer-01")
        assert result["sample"] == "SAMPLE-1"
        assert result["test"] == "glucose"
        assert result["value"] == 13.0
        assert result["status"] == "received"

    @pytest.mark.parametrize("sample", ["", None, "   ", "X" * 101, 123])
    def test_invalid_sample_id(self, open_gateway, sample):
        with pytest.raises(DeviceInputError):
            gw.receive_device_result(sample, "glucose", "1")

    @pytest.mark.parametrize("test", ["", None, "  ", "Y" * 101, 5])
    def test_invalid_test(self, open_gateway, test):
        with pytest.raises(DeviceInputError):
            gw.receive_device_result("SAMPLE-1", test, "1")

    @pytest.mark.parametrize("value", [None, "not-a-number", object(), 1e12, -1e12])
    def test_invalid_value(self, open_gateway, value):
        with pytest.raises(DeviceInputError):
            gw.receive_device_result("SAMPLE-1", "glucose", value)

    def test_numeric_string_and_int_accepted(self, open_gateway):
        assert gw.receive_device_result("SAMPLE-1", "glucose", 13)["value"] == 13.0
        assert gw.receive_device_result("SAMPLE-1", "glucose", "13.5")["value"] == 13.5


class TestDeviceAuthentication:
    def test_valid_signed_message_accepted(self, secure_gateway):
        gateway, _ = secure_gateway
        payload = _signed()
        result = gw.receive_device_result(**payload)
        assert result["status"] == "received"
        assert result["value"] == 13.0

    def test_unknown_device_rejected(self, secure_gateway):
        with pytest.raises(DeviceAuthError, match="allowed device"):
            gw.receive_device_result(**_signed(device="rogue-analyzer"))

    def test_missing_timestamp_rejected(self, secure_gateway):
        payload = _signed(timestamp=0)
        with pytest.raises(DeviceAuthError, match="timestamp"):
            gw.receive_device_result(**payload)

    def test_stale_timestamp_rejected(self, secure_gateway):
        payload = _signed(timestamp=int(time.time()) - 10_000)
        with pytest.raises(DeviceAuthError, match="timestamp"):
            gw.receive_device_result(**payload)

    def test_future_timestamp_outside_window_rejected(self, secure_gateway):
        payload = _signed(timestamp=int(time.time()) + 10_000)
        with pytest.raises(DeviceAuthError, match="timestamp"):
            gw.receive_device_result(**payload)

    def test_missing_signature_rejected(self, secure_gateway):
        payload = _signed()
        payload["signature"] = ""
        with pytest.raises(DeviceAuthError, match="signature"):
            gw.receive_device_result(**payload)

    def test_tampered_signature_rejected(self, secure_gateway):
        payload = _signed()
        payload["signature"] = "0" * 64
        with pytest.raises(DeviceAuthError, match="Invalid message signature"):
            gw.receive_device_result(**payload)

    def test_tampered_value_rejected(self, secure_gateway):
        payload = _signed(value="13.0")
        payload["value"] = "99.0"  # signature no longer matches
        with pytest.raises(DeviceAuthError):
            gw.receive_device_result(**payload)

    def test_missing_nonce_rejected(self, secure_gateway):
        payload = _signed(nonce="")
        with pytest.raises(DeviceAuthError, match="nonce"):
            gw.receive_device_result(**payload)


class TestReplayProtection:
    def test_same_nonce_rejected_second_time(self, secure_gateway):
        payload = _signed(nonce="nonce-replay")
        first = gw.receive_device_result(**payload)
        assert first["status"] == "received"
        with pytest.raises(DeviceAuthError, match="Replayed nonce"):
            gw.receive_device_result(**payload)

    def test_distinct_nonce_accepted(self, secure_gateway):
        gw.receive_device_result(**_signed(nonce="n-1"))
        assert gw.receive_device_result(**_signed(nonce="n-2"))["status"] == "received"

    def test_nonce_store_outage_fails_closed(self, secure_gateway, monkeypatch):
        # Regression for F-070: a Redis outage must NOT silently disable replay
        # protection (HMAC alone cannot stop replay of a captured message).
        monkeypatch.setattr("app.security.redis_client.cache", _BrokenCache())
        with pytest.raises(DeviceAuthError, match="replay store unavailable"):
            gw.receive_device_result(**_signed(nonce="n-outage"))

    def test_new_nonce_same_result_is_distinct_event(self, secure_gateway):
        # Documented limitation: business-level idempotency (sample+test) is not
        # implemented here; only nonce replay is blocked. We assert the current
        # honest behavior rather than claiming full deduplication.
        gw.receive_device_result(**_signed(nonce="n-A"))
        assert gw.receive_device_result(**_signed(nonce="n-B"))["status"] == "received"


class TestSignatureContract:
    def test_signature_is_over_float_formatted_value(self, secure_gateway):
        # Pin the contract: value "13" is signed as "13.0" by the gateway. A
        # device signing the literal "13" is rejected — documented, not a bug.
        ts = int(time.time())
        msg = f"analyzer-01:SAMPLE-1:glucose:13.0:{ts}".encode()
        import hashlib
        import hmac
        signature = hmac.new(b"synthetic-hmac-key", msg, hashlib.sha256).hexdigest()
        result = gw.receive_device_result(
            "SAMPLE-1", "glucose", 13, device_id="analyzer-01",
            signature=signature, timestamp=ts, nonce="contract-1",
        )
        assert result["value"] == 13.0


class TestSyntheticAstmHl7Parsing:
    """Synthetic instrument messages — no live device (Phase D scope)."""

    def test_astm_result_parsing(self):
        from app.lims.integration.astm import parse_astm_message

        message = (
            "H|\\^&|||LIS\r"
            "P|SYNTH-SPEC-1\r"
            "O|1|SYNTH-SPEC-1||GLU\r"
            "R|1|^^^GLU|Glucose|95|mg/dL|70-110|N\r"
            "L|1|N\r"
        )
        results = parse_astm_message(message)
        assert len(results) == 1
        result = results[0]
        assert result.specimen_id == "SYNTH-SPEC-1"
        assert result.test_name == "Glucose"
        assert result.value == "95"
        assert result.unit == "mg/dL"
        assert result.ref_range == "70-110"
        assert result.flag == "N"

    def test_astm_missing_result_yields_no_results(self):
        from app.lims.integration.astm import parse_astm_message

        assert parse_astm_message("H|\\^&|||LIS\rL|1|N\r") == []

    def test_hl7_oru_result_parsing(self):
        from app.lims.integration.hl7 import parse_oru_message

        message = (
            "MSH|^~\\&|ANALYZER|LAB|GULA|LAB|20261117100000||ORU^R01|MSG-1|P|2.5\r"
            "PID|1||SYNTH-PAT-1||Doe^John\r"
            "OBR|1|ORDER-1|SYNTH-SPEC-1|GLU^Glucose\r"
            # NOTE: this deployment's parser reads the specimen id from SPM-1
            # (not the HL7-standard SPM-2), and SPM must precede OBX. The
            # mapping discrepancy is recorded as a residual finding.
            "SPM|SYNTH-SPEC-1^Specimen\r"
            "OBX|1|NM|GLU^Glucose||95|mg/dL|70-110|N|||F\r"
        )
        results = parse_oru_message(message)
        assert len(results) == 1
        result = results[0]
        assert result.patient_id == "SYNTH-PAT-1"
        assert result.specimen_id == "SYNTH-SPEC-1"
        assert result.test_code == "GLU"
        assert result.value == "95"
        assert result.unit == "mg/dL"
        assert result.abnormal_flag == "N"
        assert result.result_status == "F"

    def test_critical_flag_is_retained_for_downstream_alerting(self):
        from app.lims.integration.hl7 import parse_oru_message

        message = (
            "MSH|^~\\&|ANALYZER|LAB|GULA|LAB|20261117100000||ORU^R01|MSG-2|P|2.5\r"
            "OBX|1|NM|K^Potassium||7.5|mmol/L|3.5-5.1|HH|||F\r"
        )
        result = parse_oru_message(message)[0]
        assert result.abnormal_flag == "HH"  # critical flag preserved for check_critical()
