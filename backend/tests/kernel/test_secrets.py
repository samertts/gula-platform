from __future__ import annotations

import os

import pytest

from backend.app.kernel.config.secrets import SecretsLoader


class TestSecretsLoader:
    def test_load_from_env(self):
        os.environ["KRNL_SECRET"] = "s3cr3t"
        sl = SecretsLoader()
        sl.load_from_env(prefix="KRNL_")
        assert sl.get("KRNL_SECRET") == "s3cr3t"

    def test_get_required(self):
        os.environ["REQ_SECRET"] = "required_value"
        sl = SecretsLoader()
        sl.load_from_env(prefix="REQ_")
        assert sl.get_required("REQ_SECRET") == "required_value"
        with pytest.raises(KeyError):
            sl.get_required("NONEXISTENT")
