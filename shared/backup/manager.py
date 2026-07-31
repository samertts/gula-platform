from __future__ import annotations

import gzip
import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger("gula.backup")


class BackupStrategy(ABC):
    @abstractmethod
    def backup(self, destination: str) -> str:
        ...

    @abstractmethod
    def restore(self, source: str) -> bool:
        ...


@dataclass
class FullBackup(BackupStrategy):
    db_url: str = ""
    db_name: str = "gula"

    def backup(self, destination: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{destination}/{self.db_name}_{timestamp}.sql.gz"
        cmd = [
            "pg_dump",
            "--no-owner",
            "--no-acl",
            self.db_url,
        ]
        try:
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                with gzip.open(filename, "wb") as f:
                    if proc.stdout:
                        f.write(proc.stdout.read())
                _, stderr = proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"pg_dump failed: {stderr.decode()}")
            logger.info("Backup saved to %s", filename)
            return filename
        except FileNotFoundError:
            logger.error("pg_dump not found. Install PostgreSQL client tools.")
            raise

    def restore(self, source: str) -> bool:
        try:
            with gzip.open(source, "rb") as f:
                content = f.read()
            proc = subprocess.run(
                ["psql", self.db_url],
                input=content,
                capture_output=True,
                timeout=300,
            )
            if proc.returncode != 0:
                logger.error("Restore failed: %s", proc.stderr.decode())
                return False
            logger.info("Restored from %s", source)
            return True
        except Exception as exc:
            logger.error("Restore failed: %s", exc)
            return False


@dataclass
class TableBackup(BackupStrategy):
    db_url: str = ""
    tables: list[str] | None = None

    def backup(self, destination: str) -> str:
        if not self.tables:
            raise ValueError("No tables specified for backup")
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{destination}/tables_{timestamp}.sql.gz"
        for table in self.tables:
            cmd = ["pg_dump", "--no-owner", "--no-acl", "--table", table, self.db_url]
            try:
                with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                    with gzip.open(filename, "ab") as f:
                        if proc.stdout:
                            f.write(b"\n-- Table: " + table.encode() + b"\n")
                            f.write(proc.stdout.read())
                    _, stderr = proc.communicate()
                    if proc.returncode != 0:
                        logger.warning("Table %s backup warning: %s", table, stderr.decode())
            except FileNotFoundError:
                logger.error("pg_dump not found")
                raise
        return filename

    def restore(self, source: str) -> bool:
        try:
            with gzip.open(source, "rb") as f:
                content = f.read()
            proc = subprocess.run(
                ["psql", self.db_url],
                input=content,
                capture_output=True,
                timeout=300,
            )
            return proc.returncode == 0
        except Exception as exc:
            logger.error("Restore failed: %s", exc)
            return False


class BackupManager:
    def __init__(self, strategy: BackupStrategy):
        self._strategy = strategy

    def create_backup(self, destination: str = "/tmp/backups") -> str:
        import os
        os.makedirs(destination, exist_ok=True)
        return self._strategy.backup(destination)

    def restore_from(self, source: str) -> bool:
        return self._strategy.restore(source)
