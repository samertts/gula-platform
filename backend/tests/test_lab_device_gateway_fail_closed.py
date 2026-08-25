from __future__ import annotations

from pathlib import Path

import pytest
from app.gateways import lab_device_gateway as gateway


def test_legacy_gateway_rejects_every_envelope_before_processing() -> None:
    with pytest.raises(gateway.DeviceAuthError, match="intake is disabled"):
        gateway.receive_device_result(
            "SYNTHETIC-SAMPLE-001",
            "GLUCOSE",
            101.2,
            device_id="ANALYZER-001",
            _signature="synthetic-signature",
            _timestamp=1,
            _nonce="synthetic-nonce",
        )


def test_legacy_gateway_has_no_active_auth_or_replay_acceptance_path() -> None:
    source = gateway.__file__
    assert source is not None
    content = Path(source).read_text(encoding="utf-8")

    assert "hmac.new" not in content
    assert "cache.set" not in content
    assert "LabResult" not in content
    assert "commit(" not in content
