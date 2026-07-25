from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

from pydantic import BaseModel

from security.modules.audit.models import AuditEvent

logger = logging.getLogger(__name__)

MERKLE_ROOT_INTERVAL = 100


class ImmutableLogEntry(BaseModel):
    """Internal log entry for immutable chain."""
    index: int
    event_id: str
    timestamp: str
    data_hash: str
    previous_hash: str
    signature: str = ""
    merkle_root: Optional[str] = None


class ImmutableAuditLog:
    def __init__(self, storage_path: Optional[str] = None, signing_key: Optional[bytes] = None):
        self.storage_path = Path(storage_path) if storage_path else Path(tempfile.gettempdir()) / "gula-audit"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._chain: List[ImmutableLogEntry] = []
        self._entries: List[AuditEvent] = []
        self._chain_file = self.storage_path / "audit_chain.jsonl"
        self._merkle_file = self.storage_path / "merkle_roots.jsonl"
        self.current_hash: str = "0" * 64

        if signing_key:
            self._signing_key = signing_key
        else:
            self._signing_key = Fernet.generate_key()

        self._load_chain()
        self._fernet = Fernet(self._signing_key if isinstance(self._signing_key, bytes) else self._signing_key.encode())

    def append(self, event: AuditEvent) -> ImmutableLogEntry:
        entry_hash = hashlib.sha256(
            f"{event.event_id}:{event.timestamp.isoformat()}:{event.action}:{event.actor_id}:{self.current_hash}".encode()
        ).hexdigest()

        previous_hash = self.current_hash

        entry = ImmutableLogEntry(
            index=len(self._chain),
            event_id=event.event_id,
            timestamp=event.timestamp.isoformat(),
            data_hash=entry_hash,
            previous_hash=previous_hash,
            signature="",
        )

        signature_data = f"{entry.index}:{entry.event_id}:{entry.timestamp}:{entry.previous_hash}"
        entry.signature = self._sign_entry(signature_data)

        if len(self._chain) > 0 and (len(self._chain) % MERKLE_ROOT_INTERVAL) == 0:
            entry.merkle_root = self._compute_merkle_root()

        self._chain.append(entry)
        self._entries.append(event)
        self.current_hash = entry_hash

        self._persist_entry(entry)

        return entry

    def _sign_entry(self, data: str) -> str:
        return hmac.new(
            self._signing_key if isinstance(self._signing_key, bytes) else self._signing_key.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _compute_merkle_root(self) -> str:
        if not self._chain:
            return "0" * 64

        leaf_hashes = [e.data_hash for e in self._chain[-MERKLE_ROOT_INTERVAL:]]
        while len(leaf_hashes) > 1:
            new_level: List[str] = []
            for i in range(0, len(leaf_hashes), 2):
                if i + 1 < len(leaf_hashes):
                    combined = leaf_hashes[i] + leaf_hashes[i + 1]
                else:
                    combined = leaf_hashes[i] + leaf_hashes[i]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            leaf_hashes = new_level

        return leaf_hashes[0]

    def _persist_entry(self, entry: ImmutableLogEntry) -> None:
        try:
            with open(self._chain_file, "a") as f:
                f.write(json.dumps(self._entry_to_dict(entry)) + "\n")
        except IOError as e:
            logger.error(f"Failed to persist audit entry: {e}")

    def _entry_to_dict(self, entry: ImmutableLogEntry) -> Dict[str, Any]:
        return {
            "index": entry.index,
            "event_id": entry.event_id,
            "timestamp": entry.timestamp,
            "data_hash": entry.data_hash,
            "previous_hash": entry.previous_hash,
            "signature": entry.signature,
            "merkle_root": entry.merkle_root,
        }

    def _load_chain(self) -> None:
        if self._chain_file.exists():
            try:
                with open(self._chain_file) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            entry = ImmutableLogEntry(**data)
                            self._chain.append(entry)
                if self._chain:
                    self.current_hash = self._chain[-1].data_hash
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load audit chain: {e}")

    def verify_integrity(self) -> Dict[str, Any]:
        violations: List[str] = []
        passed = True

        for i in range(1, len(self._chain)):
            expected_prev = self._chain[i - 1].data_hash
            actual_prev = self._chain[i].previous_hash
            if expected_prev != actual_prev:
                violations.append(f"Chain break at index {i}: expected {expected_prev[:16]}..., got {actual_prev[:16]}...")
                passed = False

        for entry in self._chain:
            sig_data = f"{entry.index}:{entry.event_id}:{entry.timestamp}:{entry.previous_hash}"
            expected_sig = self._sign_entry(sig_data)
            if entry.signature != expected_sig:
                violations.append(f"Signature mismatch for entry {entry.index} (event {entry.event_id})")
                passed = False

        return {
            "valid": passed,
            "entries_checked": len(self._chain),
            "violations": violations,
            "first_violation_index": violations[0] if violations else None,
        }

    def detect_tampering(self) -> Dict[str, Any]:
        integrity = self.verify_integrity()
        tampered = not integrity["valid"]

        findings: List[str] = []
        if tampered:
            findings = integrity["violations"]

        if os.path.exists(self._chain_file):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(self._chain_file), tz=timezone.utc)
            findings.append(f"Chain file last modified: {file_mtime.isoformat()}")

        return {
            "tampered": tampered,
            "findings": findings,
            "integrity_check": integrity,
        }

    def get_chain_verification_tool(self) -> str:
        lines = [
            "#!/usr/bin/env python3",
            '"""GULA Audit Chain Verification Tool"""',
            "",
            "import hashlib, hmac, json, sys",
            "",
            "def verify_chain(chain_file, signing_key):",
            "    with open(chain_file) as f:",
            "        chain = [json.loads(line) for line in f if line.strip()]",
            "",
            "    for i in range(1, len(chain)):",
            "        expected = chain[i-1]['data_hash']",
            "        actual = chain[i]['previous_hash']",
            "        if expected != actual:",
            "            print(f'CHAIN BREAK at index {i}: {actual[:16]}... != {expected[:16]}...')",
            "            return False",
            "",
            "    for entry in chain:",
            "        sig_data = f\"{entry['index']}:{entry['event_id']}:{entry['timestamp']}:{entry['previous_hash']}\"",
            "        expected_sig = hmac.new(signing_key.encode(), sig_data.encode(), hashlib.sha256).hexdigest()",
            "        if entry['signature'] != expected_sig:",
            "            print(f'SIGNATURE MISMATCH at index {entry[\"index\"]}')",
            "            return False",
            "",
            "    print(f'Chain verified: {len(chain)} entries intact')",
            "    return True",
            "",
            'if __name__ == "__main__":',
            '    if len(sys.argv) < 3:',
            '        print("Usage: verify_chain.py <chain_file> <signing_key>")',
            "        sys.exit(1)",
            "    result = verify_chain(sys.argv[1], sys.argv[2])",
            "    sys.exit(0 if result else 1)",
        ]
        return "\n".join(lines)

    def get_forensic_analysis(self, event_id: str) -> Dict[str, Any]:
        for i, entry in enumerate(self._chain):
            if entry.event_id == event_id:
                context_start = max(0, i - 3)
                context_end = min(len(self._chain), i + 4)
                surrounding_entries = self._chain[context_start:context_end]

                chain_proof: Dict[str, Any] = {
                    "target_entry": self._entry_to_dict(entry),
                    "target_index": i,
                    "chain_length": len(self._chain),
                    "surrounding_entries": [self._entry_to_dict(e) for e in surrounding_entries],
                    "is_chain_intact": self.verify_integrity()["valid"],
                    "entry_position": f"entry {i + 1} of {len(self._chain)}",
                }

                if i > 0:
                    chain_proof["holder_of_previous_hash"] = self._chain[i - 1].data_hash[:16] + "..."
                if i < len(self._chain) - 1:
                    chain_proof["referenced_by_next"] = self._chain[i + 1].previous_hash[:16] + "..."

                return chain_proof

        return {"error": f"Event {event_id} not found", "chain_length": len(self._chain)}

    def publish_merkle_root(self) -> str:
        if not self._chain:
            return ""

        root = self._compute_merkle_root()
        publication = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "merkle_root": root,
            "chain_length": len(self._chain),
            "last_event_id": self._chain[-1].event_id,
        }

        with open(self._merkle_file, "a") as f:
            f.write(json.dumps(publication) + "\n")

        logger.info(f"Merkle root published: {root[:16]}... at chain length {len(self._chain)}")
        return root
