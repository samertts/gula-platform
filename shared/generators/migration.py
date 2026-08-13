from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path

logger = logging.getLogger("gula.generators.migration")

_MIGRATION_TPL = '''"""Migration: {message}

Generated: {timestamp}
"""

from __future__ import annotations

from typing import Any

from alembic import op
from sqlalchemy.engine import reflection

revision = "{revision}"
down_revision = "{down_revision}"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = reflection.Inspector.from_engine(bind)
    return column in [c["name"] for c in insp.get_columns(table)]


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    insp = reflection.Inspector.from_engine(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
'''


class MigrationGenerator:
    def __init__(self, message: str, target_dir: str = "backend/migrations/versions") -> None:
        self._message = message
        self._target_dir = Path(target_dir)
        self._ts = datetime.now(UTC)

    def generate(self) -> None:
        ts_str = self._ts.strftime("%Y%m%d_%H%M%S")
        hash_str = hashlib.sha256(self._message.encode()).hexdigest()[:8]
        revision = f"{ts_str}_{hash_str}"
        filename = f"{revision}_{self._message.lower().replace(' ', '_')[:60].strip('_')}.py"
        filepath = self._target_dir / filename
        self._target_dir.mkdir(parents=True, exist_ok=True)
        if filepath.exists():
            logger.warning("Migration already exists: %s", filepath)
            return
        down_revision = self._get_head_revision() or "20250322_0000_create_base_schema"
        filepath.write_text(_MIGRATION_TPL.format(
            message=self._message, timestamp=self._ts.isoformat(),
            revision=revision, down_revision=down_revision,
        ))
        logger.info("Migration created: %s", filepath)

    def _get_head_revision(self) -> str | None:
        if not self._target_dir.is_dir():
            return None
        revisions = sorted([f for f in self._target_dir.iterdir() if f.suffix == ".py"])
        if not revisions:
            return None
        head = revisions[-1].read_text()
        for line in head.splitlines():
            if line.startswith("revision"):
                return line.split("=")[1].strip().strip('"\'')
        return None


__all__ = ["MigrationGenerator"]
