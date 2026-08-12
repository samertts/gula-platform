"""Adapter-mode unit tests — verifies stub/live/shadow resolution.

These tests stay in stub mode (no network). They assert:
  - resolve_mode() respects the per-adapter override before the global.
  - Missing required credentials cleanly downgrade LIVE → STUB.
  - The stub response from each adapter has the correct schema.
  - The Cloudflare stub reports `configured=False` when CF_ZONE_ID absent.
"""
import importlib.util
import os
import sys
import types

# ─── Env + stub app.config so identity.py imports work standalone ──────────
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)

_BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_cfg = types.ModuleType("app.config")
class _S:
    NID_HMAC_KEY = "a" * 64
_cfg.settings = _S()
sys.modules.setdefault("app.config", _cfg)


# ─── Import the mode module (no fastapi needed) ────────────────────────────
def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_mode = _load(
    "app.gateways.mode",
    os.path.join(_BACKEND, "app", "gateways", "mode.py"),
)
AdapterMode = _mode.AdapterMode
resolve_mode = _mode.resolve_mode


# ─── resolve_mode() tests ───────────────────────────────────────────────────

class TestResolveMode:
    def test_default_is_stub(self, monkeypatch):
        for k in list(os.environ):
            if k.startswith("GULA_ADAPTER_MODE"):
                monkeypatch.delenv(k, raising=False)
        assert resolve_mode("nid") is AdapterMode.STUB

    def test_global_default_respected(self, monkeypatch):
        monkeypatch.setenv("GULA_ADAPTER_MODE", "live")
        monkeypatch.setenv("FOO_URL", "x")
        monkeypatch.setenv("FOO_KEY", "y")
        assert resolve_mode("foo", ("FOO_URL", "FOO_KEY")) is AdapterMode.LIVE

    def test_per_adapter_override_wins(self, monkeypatch):
        monkeypatch.setenv("GULA_ADAPTER_MODE", "stub")
        monkeypatch.setenv("GULA_ADAPTER_MODE_NID", "shadow")
        monkeypatch.setenv("MOI_NID_API_URL", "x")
        monkeypatch.setenv("MOI_NID_API_KEY", "y")
        assert resolve_mode("nid", ("MOI_NID_API_URL", "MOI_NID_API_KEY")) is AdapterMode.SHADOW

    def test_missing_credentials_downgrades(self, monkeypatch):
        monkeypatch.setenv("GULA_ADAPTER_MODE_NID", "live")
        monkeypatch.delenv("MOI_NID_API_URL", raising=False)
        monkeypatch.delenv("MOI_NID_API_KEY", raising=False)
        assert resolve_mode("nid", ("MOI_NID_API_URL", "MOI_NID_API_KEY")) is AdapterMode.STUB

    def test_invalid_mode_falls_back(self, monkeypatch):
        monkeypatch.setenv("GULA_ADAPTER_MODE_XYZ", "turbo")
        assert resolve_mode("xyz") is AdapterMode.STUB

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("GULA_ADAPTER_MODE_NID", "LIVE")
        monkeypatch.setenv("MOI_NID_API_URL", "x")
        monkeypatch.setenv("MOI_NID_API_KEY", "y")
        assert resolve_mode("nid", ("MOI_NID_API_URL", "MOI_NID_API_KEY")) is AdapterMode.LIVE


# ─── Per-adapter stub-response shape ────────────────────────────────────────
# We bypass the fastapi-dependent parts of each gateway module by loading
# just the stub helpers via direct method calls.

class TestStubResponses:
    def _make_gw(self, path_rel: str, cls_name: str, monkeypatch):
        """Load a gateway module standalone (no fastapi in app.*)."""
        for k in list(os.environ):
            if k.startswith("GULA_ADAPTER_MODE"):
                monkeypatch.delenv(k, raising=False)
        mod = _load(
            f"app.gateways.{path_rel.replace('/', '.').replace('.py','')}",
            os.path.join(_BACKEND, "app", "gateways", path_rel),
        )
        cls = getattr(mod, cls_name)
        return cls()

    def test_nid_stub_invalid_length(self, monkeypatch):
        gw = self._make_gw("national_identity_gateway.py", "NationalIdentityGateway", monkeypatch)
        r = gw._stub_response("123")  # too short
        assert r["valid"] is False
        assert r["source"].startswith("stub_")

    def test_nid_stub_valid_length(self, monkeypatch):
        gw = self._make_gw("national_identity_gateway.py", "NationalIdentityGateway", monkeypatch)
        r = gw._stub_response("1" * 12)
        assert r["valid"] is True
        assert r["source"].startswith("stub_")

    def test_insurance_stub(self, monkeypatch):
        gw = self._make_gw("insurance_gateway.py", "InsuranceGateway", monkeypatch)
        assert gw._stub_response("")["insured"] is False
        assert gw._stub_response("ABC123")["insured"] is True

    def test_residency_stub_invalid_passport(self, monkeypatch):
        gw = self._make_gw("residency_gateway.py", "ResidencyGateway", monkeypatch)
        r = gw._stub_response("!!", "US")
        assert r["valid"] is False

    def test_residency_stub_valid_passport(self, monkeypatch):
        gw = self._make_gw("residency_gateway.py", "ResidencyGateway", monkeypatch)
        r = gw._stub_response("ABC12345", "us")
        assert r["valid"] is True
        assert r["nationality"] == "US"

    def test_cloudflare_stub_configured_false(self, monkeypatch):
        monkeypatch.delenv("CF_API_TOKEN", raising=False)
        monkeypatch.delenv("CF_ZONE_ID", raising=False)
        gw = self._make_gw("cloudflare_gateway.py", "CloudflareGateway", monkeypatch)
        r = gw._stub_response()
        assert r["configured"] is False
        assert r["mode"] == "stub"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
