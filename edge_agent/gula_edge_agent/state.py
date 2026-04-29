"""On-disk state for the edge agent — encrypted at rest.

State persisted:
  - device_id        (str)
  - agent_token      (str, opaque bearer for /edge/agent/* calls)
  - private_key_pem  (str, RSA 2048; never leaves the device)
  - public_key_pem   (str)
  - cert_fingerprint (str)
  - lab_id           (int)
  - last_seen_nonce  (str, last server-issued challenge)
  - completed_uids   (list[str], for ack-style cleanup on heartbeat)

The state file is encrypted with a key derived from a per-device secret
(``state.key``). The key is generated on first run and chmodded 0600.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet


class StateError(Exception):
    pass


class AgentState:
    def __init__(self, state_dir: str):
        self.dir = Path(state_dir).expanduser().resolve()
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.dir / "state.bin"
        self.key_file   = self.dir / "state.key"
        self._cipher    = self._load_or_create_cipher()
        self._cache: Optional[dict[str, Any]] = None

    # ── private ───────────────────────────────────────────────────────────────

    def _load_or_create_cipher(self) -> Fernet:
        if self.key_file.exists():
            return Fernet(self.key_file.read_bytes())
        key = Fernet.generate_key()
        self.key_file.write_bytes(key)
        try:
            os.chmod(self.key_file, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        return Fernet(key)

    def _read(self) -> dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if not self.state_file.exists():
            self._cache = {}
            return self._cache
        try:
            data = self.state_file.read_bytes()
            self._cache = json.loads(self._cipher.decrypt(data).decode("utf-8"))
        except Exception as e:
            raise StateError(f"corrupt state file: {e}")
        return self._cache

    def _write(self, data: dict[str, Any]) -> None:
        blob = self._cipher.encrypt(json.dumps(data).encode("utf-8"))
        self.state_file.write_bytes(blob)
        try:
            os.chmod(self.state_file, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        self._cache = data

    # ── public ────────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._read().get(key, default)

    def set(self, **fields: Any) -> None:
        data = self._read()
        data.update(fields)
        self._write(data)

    def is_registered(self) -> bool:
        d = self._read()
        return bool(d.get("device_id") and d.get("agent_token"))

    def all(self) -> dict[str, Any]:
        return dict(self._read())
