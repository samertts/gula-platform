from __future__ import annotations

from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class DBIntegrityEvaluator(DimensionEvaluator):
    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        migration_policy = self._check_migration_policy(target)
        self._add_evidence(
            "migration_policy",
            value=migration_policy,
            source="Migration files scan",
            passed=migration_policy,
        )
        if not migration_policy:
            self._add_remediation(
                "Follow migration policy: never modify existing migrations, always create new revisions",
                severity="critical",
                effort="1h",
            )

        referential_integrity = self._check_referential_integrity(target)
        self._add_evidence(
            "referential_integrity",
            value=referential_integrity,
            source="SQLAlchemy model scan",
            passed=referential_integrity,
        )
        if not referential_integrity:
            self._add_remediation(
                "Add foreign key constraints with ON DELETE CASCADE/SET NULL where appropriate",
                severity="high",
                effort="4h",
            )

        index_coverage = self._check_indexes(target)
        self._add_evidence(
            "index_coverage",
            value=index_coverage,
            source="Model/table scan",
            passed=index_coverage,
        )
        if not index_coverage:
            self._add_remediation(
                "Add database indexes on foreign keys and frequently queried columns",
                severity="high",
                effort="3h",
            )

        alembic_migrations = self._check_alembic_setup(target)
        self._add_evidence(
            "alembic_setup",
            value=alembic_migrations,
            source="Alembic config scan",
            passed=alembic_migrations,
        )
        if not alembic_migrations:
            self._add_remediation(
                "Set up Alembic for database migration management",
                severity="critical",
                effort="2h",
            )

        idempotent_migrations = self._check_idempotent_migrations(target)
        self._add_evidence(
            "idempotent_migrations",
            value=idempotent_migrations,
            source="Migration file scan",
            passed=idempotent_migrations,
        )
        if not idempotent_migrations:
            self._add_remediation(
                "Make all migrations idempotent with _has_column(), _table_exists() guards",
                severity="high",
                effort="2h",
            )

        nullable_columns = self._check_nullable_columns(target)
        self._add_evidence(
            "nullable_new_columns",
            value=nullable_columns,
            source="Migration file scan",
            passed=nullable_columns,
        )
        if not nullable_columns:
            self._add_remediation(
                "New columns must be nullable or have server_default — non-nullable breaks existing rows",
                severity="critical",
                effort="fix immediately",
            )

        optimistic_locking = self._check_optimistic_locking(target)
        self._add_evidence(
            "optimistic_locking",
            value=optimistic_locking,
            source="Model scan",
            passed=optimistic_locking,
        )
        if not optimistic_locking:
            self._add_remediation(
                "Add version column for optimistic locking on concurrent-write entities",
                severity="medium",
                effort="3h",
            )

        score = 1.0
        checks = [
            (migration_policy, 0.15),
            (referential_integrity, 0.15),
            (index_coverage, 0.15),
            (alembic_migrations, 0.15),
            (idempotent_migrations, 0.1),
            (nullable_columns, 0.15),
            (optimistic_locking, 0.05),
        ]
        for passed, penalty in checks:
            if not passed:
                score -= penalty

        return self._result(score)

    def _check_migration_policy(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            if "migration" in py_file.parts or "alembic" in py_file.parts:
                try:
                    content = py_file.read_text()
                    if "immutable" in content.lower() or "never modify" in content.lower():
                        return True
                except Exception:
                    continue
        migration_dirs = [
            target / "migrations" / "versions",
            target / "alembic" / "versions",
            target.parent / "migrations" / "versions",
        ]
        return any(d.exists() and len(list(d.glob("*.py"))) > 0 for d in migration_dirs)

    def _check_referential_integrity(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            if "model" in py_file.parts or "models" in py_file.parts:
                try:
                    content = py_file.read_text()
                    if "ForeignKey" in content or "relationship" in content:
                        return True
                except Exception:
                    continue
        return False

    def _check_indexes(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            if "model" in py_file.parts or "models" in py_file.parts:
                try:
                    content = py_file.read_text()
                    if "Index(" in content or "index=True" in content:
                        return True
                except Exception:
                    continue
        return False

    def _check_alembic_setup(self, target: Path) -> bool:
        alembic_files = [
            target / "alembic.ini",
            target.parent / "alembic.ini",
            target / "migrations" / "env.py",
            target.parent / "migrations" / "env.py",
            target / "alembic" / "env.py",
        ]
        return any(f.exists() for f in alembic_files)

    def _check_idempotent_migrations(self, target: Path) -> bool:
        migration_dirs = [
            target / "migrations" / "versions",
            target.parent / "migrations" / "versions",
            target / "alembic" / "versions",
        ]
        for d in migration_dirs:
            if not d.exists():
                continue
            for py_file in d.glob("*.py"):
                try:
                    content = py_file.read_text()
                    if "_has_column" in content or "_table_exists" in content or "_index_exists" in content:
                        return True
                except Exception:
                    continue
        return False

    def _check_nullable_columns(self, target: Path) -> bool:
        migration_dirs = [
            target / "migrations" / "versions",
            target.parent / "migrations" / "versions",
            target / "alembic" / "versions",
        ]
        for d in migration_dirs:
            if not d.exists():
                continue
            for py_file in d.glob("*.py"):
                try:
                    content = py_file.read_text()
                    if "nullable=False" in content and "server_default" not in content:
                        return False
                except Exception:
                    continue
        return True

    def _check_optimistic_locking(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            if "model" in py_file.parts or "models" in py_file.parts:
                try:
                    content = py_file.read_text()
                    if "version" in content.lower() and ("Column" in content or "Integer" in content or "Mapped" in content):
                        return True
                except Exception:
                    continue
        return False
