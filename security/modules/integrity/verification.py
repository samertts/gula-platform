from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

CRITICAL_SYSTEM_FILES: list[str] = [
    "/etc/passwd", "/etc/shadow", "/etc/sudoers", "/etc/hosts",
    "/etc/resolv.conf", "/etc/ssh/sshd_config", "/etc/nginx/nginx.conf",
    "/etc/postgresql/postgresql.conf", "/etc/redis/redis.conf",
    "/etc/rabbitmq/rabbitmq.conf",
    "/etc/kubernetes/manifests/",
    "/etc/docker/daemon.json",
]

CRITICAL_APPLICATION_PATTERNS: list[str] = [
    "**/config*.yaml", "**/config*.yml", "**/config*.json",
    "**/application*.properties", "**/.env*",
    "**/Dockerfile*", "**/docker-compose*",
    "**/*.pem", "**/*.key", "**/*.crt", "**/*.cert",
    "**/terraform.tfstate*", "**/*.tf",
    "**/kubeconfig*", "**/*.kubeconfig",
]


class IntegrityBaseline(BaseModel):
    id: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    file_hashes: dict[str, str] = Field(default_factory=dict)
    file_metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)
    config_snapshots: dict[str, str] = Field(default_factory=dict)


class IntegrityViolation(BaseModel):
    path: str
    violation_type: str
    expected: str = ""
    actual: str = ""
    severity: str = "HIGH"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    description: str = ""


class IntegrityReport(BaseModel):
    passed: bool = True
    violations: list[IntegrityViolation] = Field(default_factory=list)
    files_checked: int = 0
    total_files: int = 0


class IntegrityVerifier:
    def __init__(self, baseline_path: str | None = None):
        self.baseline_path = Path(baseline_path) if baseline_path else Path.cwd() / ".integrity-baseline.json"
        self.baseline: IntegrityBaseline | None = None
        self._load_baseline()

    def _load_baseline(self) -> None:
        if self.baseline_path.exists():
            try:
                data = json.loads(self.baseline_path.read_text())
                self.baseline = IntegrityBaseline(**data)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to load integrity baseline: {e}")

    def _save_baseline(self) -> None:
        if self.baseline:
            self.baseline_path.write_text(json.dumps(self.baseline.model_dump(mode="json"), indent=2, default=str))

    def _compute_file_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        try:
            h = hashlib.new(algorithm)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except (OSError, PermissionError) as e:
            logger.error(f"Cannot compute hash for {file_path}: {e}")
            return ""

    def _get_file_metadata(self, file_path: str) -> dict[str, Any]:
        try:
            st = os.stat(file_path)
            return {
                "size": st.st_size,
                "mode": stat.S_IMODE(st.st_mode),
                "owner": st.st_uid,
                "group": st.st_gid,
                "mtime": datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat(),
                "ctime": datetime.fromtimestamp(st.st_ctime, tz=UTC).isoformat(),
            }
        except (OSError, PermissionError):
            return {}

    def create_baseline(self, paths: list[str]) -> IntegrityBaseline:
        file_hashes: dict[str, str] = {}
        file_metadata: dict[str, dict[str, Any]] = {}

        for path in paths:
            p = Path(path)
            if p.is_file():
                fhash = self._compute_file_hash(str(p))
                if fhash:
                    file_hashes[str(p)] = fhash
                    file_metadata[str(p)] = self._get_file_metadata(str(p))
            elif p.is_dir():
                for fpath in p.rglob("*"):
                    if fpath.is_file():
                        fhash = self._compute_file_hash(str(fpath))
                        if fhash:
                            file_hashes[str(fpath)] = fhash
                            file_metadata[str(fpath)] = self._get_file_metadata(str(fpath))

        self.baseline = IntegrityBaseline(
            id=datetime.now(UTC).isoformat(),
            file_hashes=file_hashes,
            file_metadata=file_metadata,
        )

        self._save_baseline()
        logger.info(f"Created integrity baseline with {len(file_hashes)} files")
        return self.baseline

    def verify_files(self, paths: list[str] | None = None) -> IntegrityReport:
        if not self.baseline:
            return IntegrityReport(passed=False, violations=[
                IntegrityViolation(path="", violation_type="no_baseline",
                                   description="No integrity baseline found. Run create_baseline() first.")
            ])

        violations: list[IntegrityViolation] = []
        files_checked = 0

        target_files = paths or list(self.baseline.file_hashes.keys())

        for file_path in target_files:
            expected_hash = self.baseline.file_hashes.get(file_path)
            if expected_hash is None:
                continue

            if not os.path.exists(file_path):
                violations.append(IntegrityViolation(
                    path=file_path,
                    violation_type="file_missing",
                    expected="file exists",
                    actual="file not found",
                    severity="CRITICAL",
                    description=f"Monitored file '{file_path}' has been deleted",
                ))
                continue

            current_hash = self._compute_file_hash(file_path)
            files_checked += 1

            if current_hash != expected_hash:
                violations.append(IntegrityViolation(
                    path=file_path,
                    violation_type="hash_mismatch",
                    expected=expected_hash[:16] + "...",
                    actual=current_hash[:16] + "...",
                    severity="HIGH",
                    description=f"File '{file_path}' content has changed since baseline",
                ))

            current_meta = self._get_file_metadata(file_path)
            expected_meta = self.baseline.file_metadata.get(file_path, {})

            if current_meta.get("mode") != expected_meta.get("mode"):
                current_mode = oct(current_meta.get("mode", 0))
                expected_mode = oct(expected_meta.get("mode", 0))
                violations.append(IntegrityViolation(
                    path=file_path,
                    violation_type="permission_change",
                    expected=f"mode {expected_mode}",
                    actual=f"mode {current_mode}",
                    severity="MEDIUM",
                    description=f"File '{file_path}' permissions changed from {expected_mode} to {current_mode}",
                ))

            if current_meta.get("owner") != expected_meta.get("owner"):
                violations.append(IntegrityViolation(
                    path=file_path,
                    violation_type="owner_change",
                    expected=f"uid {expected_meta.get('owner')}",
                    actual=f"uid {current_meta.get('owner')}",
                    severity="HIGH",
                    description=f"File '{file_path}' owner changed",
                ))

        report = IntegrityReport(
            passed=len(violations) == 0,
            violations=violations,
            files_checked=files_checked,
            total_files=len(target_files),
        )

        if violations:
            logger.warning(f"Integrity violations found: {len(violations)} in {files_checked} files")

        return report

    def verify_binary_signatures(self, binary_paths: list[str],
                                  public_key_pem: str | None = None) -> dict[str, Any]:
        findings: list[str] = []
        passed = True
        signed = 0
        unsigned = 0

        for path in binary_paths:
            if not os.path.exists(path):
                findings.append(f"Binary not found: {path}")
                passed = False
                continue

            p = Path(path)
            sig_path = p.with_suffix(p.suffix + ".sig")
            if sig_path.exists():
                signed += 1
                if public_key_pem:
                    try:
                        public_key = serialization.load_pem_public_key(public_key_pem.encode())
                        binary_data = p.read_bytes()
                        signature = sig_path.read_bytes()

                        if isinstance(public_key, ed25519.Ed25519PublicKey):
                            public_key.verify(signature, binary_data)
                        elif isinstance(public_key, rsa.RSAPublicKey):
                            public_key.verify(
                                signature, binary_data,
                                padding.PKCS1v15(), hashes.SHA256()
                            )
                        else:
                            findings.append(f"Unsupported key type for {path}")
                            passed = False
                            continue
                    except InvalidSignature:
                        findings.append(f"Invalid signature for {path}")
                        passed = False
                    except Exception as e:
                        findings.append(f"Signature verification error for {path}: {e}")
                        passed = False
            else:
                unsigned += 1
                findings.append(f"No signature file found for {path}")
                passed = False

        return {
            "passed": passed,
            "signed": signed,
            "unsigned": unsigned,
            "total": len(binary_paths),
            "findings": findings,
        }

    def verify_database_integrity(self, db_path: str) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        if not os.path.exists(db_path):
            return {"passed": False, "findings": ["Database file not found"]}

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            if integrity_result != "ok":
                findings.append(f"Database integrity check failed: {integrity_result}")
                passed = False

            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                row_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            if fk_violations:
                findings.append(f"Foreign key violations found: {len(fk_violations)}")
                passed = False

            conn.close()

            findings.append(f"Database OK: {page_count} pages, {page_size} bytes/page, {len(tables)} tables")

        except (sqlite3.Error, Exception) as e:
            findings.append(f"Database verification error: {e}")
            passed = False

        return {"passed": passed, "findings": findings}

    def detect_config_drift(self, config_files: dict[str, str]) -> IntegrityReport:
        if not self.baseline:
            return IntegrityReport(passed=False, violations=[
                IntegrityViolation(path="", violation_type="no_baseline",
                                   description="No baseline for drift detection")
            ])

        violations: list[IntegrityViolation] = []

        for path, expected_content in config_files.items():
            if not os.path.exists(path):
                violations.append(IntegrityViolation(
                    path=path, violation_type="missing",
                    description=f"Configuration file '{path}' is missing",
                ))
                continue

            try:
                actual_content = Path(path).read_text()
                actual_normalized = re.sub(r"\s+", "", actual_content)
                expected_normalized = re.sub(r"\s+", "", expected_content)

                if actual_normalized != expected_normalized:
                    current_hash = hashlib.sha256(actual_content.encode()).hexdigest()
                    expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()
                    violations.append(IntegrityViolation(
                        path=path,
                        violation_type="config_drift",
                        expected=expected_hash[:16] + "...",
                        actual=current_hash[:16] + "...",
                        severity="HIGH",
                        description=f"Configuration drift detected for '{path}'",
                    ))
            except OSError as e:
                violations.append(IntegrityViolation(
                    path=path, violation_type="read_error",
                    description=f"Cannot read '{path}': {e}",
                ))

        return IntegrityReport(
            passed=len(violations) == 0,
            violations=violations,
            files_checked=len(config_files),
            total_files=len(config_files),
        )

    def monitor_critical_files(self, custom_paths: list[str] | None = None) -> IntegrityReport:
        watch_paths = custom_paths or CRITICAL_SYSTEM_FILES
        existing_paths = [p for p in watch_paths if os.path.exists(p)]

        if not self.baseline:
            self.create_baseline(existing_paths)

        return self.verify_files(existing_paths)

    def compare_with_baseline(self, new_baseline: IntegrityBaseline) -> dict[str, Any]:
        if not self.baseline:
            return {"passed": False, "message": "No existing baseline to compare against"}

        added: list[str] = []
        removed: list[str] = []
        changed: list[str] = []

        old_hashes = self.baseline.file_hashes
        new_hashes = new_baseline.file_hashes

        for path in new_hashes:
            if path not in old_hashes:
                added.append(path)
            elif new_hashes[path] != old_hashes[path]:
                changed.append(path)

        for path in old_hashes:
            if path not in new_hashes:
                removed.append(path)

        return {
            "added_files": added,
            "removed_files": removed,
            "changed_files": changed,
            "total_added": len(added),
            "total_removed": len(removed),
            "total_changed": len(changed),
            "passed": len(added) == 0 and len(removed) == 0 and len(changed) == 0,
        }
