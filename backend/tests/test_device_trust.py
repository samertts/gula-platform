"""Tests for the Device Trust Service."""

from app.services.device_trust_service import (
    DeviceTrustService,
    DeviceFingerprint,
    TrustLevel,
    DevicePlatform,
    compute_device_fingerprint,
)


class TestDeviceFingerprint:
    def test_compute_fingerprint(self):
        fp = compute_device_fingerprint(
            user_agent="Mozilla/5.0 Chrome/120.0",
            platform="web",
            screen_resolution="1920x1080",
            language="en-US",
            timezone="Asia/Baghdad",
            hardware_concurrency=8,
            device_memory=4.0,
        )
        assert fp.device_id
        assert fp.platform == DevicePlatform.WEB
        assert fp.hardware_concurrency == 8
        assert fp.device_memory == 4.0

    def test_same_input_same_hash(self):
        fp1 = compute_device_fingerprint(
            user_agent="Same UA",
            platform="android",
        )
        fp2 = compute_device_fingerprint(
            user_agent="Same UA",
            platform="android",
        )
        assert fp1.device_id == fp2.device_id

    def test_different_input_different_hash(self):
        fp1 = compute_device_fingerprint(
            user_agent="UA 1",
            platform="web",
        )
        fp2 = compute_device_fingerprint(
            user_agent="UA 2",
            platform="web",
        )
        assert fp1.device_id != fp2.device_id


class TestDeviceTrustService:
    def test_register_device(self):
        svc = DeviceTrustService()
        fp = compute_device_fingerprint(
            user_agent="Mozilla/5.0",
            platform="web",
            language="ar-IQ",
        )
        device = svc.register_device("user-001", fp, device_name="Home PC")
        assert device.device_id
        assert device.user_id == "user-001"
        assert device.device_name == "Home PC"
        assert device.trust_level == TrustLevel.UNKNOWN

    def test_register_duplicate_fingerprint(self):
        svc = DeviceTrustService()
        fp = compute_device_fingerprint(
            user_agent="Duplicate UA",
            platform="web",
        )
        d1 = svc.register_device("user-001", fp)
        d2 = svc.register_device("user-001", fp)
        assert d1.device_id == d2.device_id

    def test_get_device(self):
        svc = DeviceTrustService()
        fp = compute_device_fingerprint(user_agent="Get Test", platform="web")
        registered = svc.register_device("user-001", fp)
        found = svc.get_device(registered.device_id)
        assert found is not None
        assert found.device_id == registered.device_id

    def test_get_user_devices(self):
        svc = DeviceTrustService()
        fp1 = compute_device_fingerprint(user_agent="UA 1", platform="web")
        fp2 = compute_device_fingerprint(user_agent="UA 2", platform="android")
        svc.register_device("user-001", fp1, device_name="Laptop")
        svc.register_device("user-001", fp2, device_name="Phone")
        devices = svc.get_user_devices("user-001")
        assert len(devices) == 2

    def test_trust_level_escalation(self):
        svc = DeviceTrustService()
        fp = compute_device_fingerprint(user_agent="Trust Escalate", platform="web")
        device = svc.register_device("user-001", fp)
        assert device.trust_level == TrustLevel.UNKNOWN

        svc.record_successful_login(device.device_id)
        assert device.trust_level == TrustLevel.LOW

        svc.record_successful_login(device.device_id)
        assert device.trust_level == TrustLevel.MEDIUM

        svc.record_successful_login(device.device_id)
        assert device.trust_level == TrustLevel.MEDIUM

        for _ in range(2):
            svc.record_successful_login(device.device_id)
        assert device.trust_level == TrustLevel.HIGH

        for _ in range(5):
            svc.record_successful_login(device.device_id)
        assert device.trust_level == TrustLevel.TRUSTED

    def test_device_deactivation_on_failed_attempts(self):
        svc = DeviceTrustService()
        fp = compute_device_fingerprint(user_agent="Fail Test", platform="web")
        device = svc.register_device("user-001", fp)

        for _ in range(5):
            svc.record_failed_attempt(device.device_id)

        assert device.is_active is False
        assert device.trust_level == TrustLevel.LOW

    def test_verify_device(self):
        svc = DeviceTrustService()
        fp = compute_device_fingerprint(user_agent="Verify Test", platform="web")
        device = svc.register_device("user-001", fp)
        assert svc.verify_device(device.device_id, fp)
        wrong_fp = compute_device_fingerprint(user_agent="Wrong", platform="web")
        assert not svc.verify_device(device.device_id, wrong_fp)

    def test_deactivate_device(self):
        svc = DeviceTrustService()
        fp = compute_device_fingerprint(user_agent="Deact Test", platform="web")
        device = svc.register_device("user-001", fp)
        assert svc.deactivate_device(device.device_id)
        assert device.is_active is False

    def test_set_current_device(self):
        svc = DeviceTrustService()
        fp1 = compute_device_fingerprint(user_agent="Current 1", platform="web")
        fp2 = compute_device_fingerprint(user_agent="Current 2", platform="android")
        d1 = svc.register_device("user-001", fp1)
        d2 = svc.register_device("user-001", fp2)

        svc.set_current_device("user-001", d1.device_id)
        assert d1.is_current
        assert not d2.is_current

        svc.set_current_device("user-001", d2.device_id)
        assert d2.is_current
        assert not d1.is_current
