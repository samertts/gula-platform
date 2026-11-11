from pathlib import Path

from scripts import data_preservation_gate as gate


def _write_model_tree(tmp_path: Path, source: str) -> None:
    models = tmp_path / "models"
    models.mkdir()
    (models / "base.py").write_text("", encoding="utf-8")
    (models / "fixture.py").write_text(source, encoding="utf-8")


def test_inventory_recognizes_direct_soft_delete_fields(tmp_path, monkeypatch):
    _write_model_tree(
        tmp_path,
        """
from sqlalchemy import Column, Boolean, DateTime
from .base import Base

class Patient(Base):
    __tablename__ = 'patients'
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
""",
    )
    monkeypatch.setattr(gate, "MODELS_DIR", tmp_path / "models")
    entries = gate._model_inventory()
    assert len(entries) == 1
    assert entries[0].table == "patients"
    assert entries[0].fields == ("deleted_at", "is_deleted")
    assert entries[0].category == "protected_business"


def test_inventory_recognizes_inherited_soft_delete_mixin(tmp_path, monkeypatch):
    _write_model_tree(
        tmp_path,
        """
from .base import Base, SoftDeleteMixin

class AuditedEntity(SoftDeleteMixin):
    pass

class Order(AuditedEntity, Base):
    __tablename__ = 'lab_orders'
""",
    )
    monkeypatch.setattr(gate, "MODELS_DIR", tmp_path / "models")
    entries = gate._model_inventory()
    assert len(entries) == 1
    assert entries[0].inherited_soft_delete is True


def test_inventory_keeps_lifecycle_exceptions_explicit(tmp_path, monkeypatch):
    _write_model_tree(
        tmp_path,
        """
from .base import Base

class Audit(Base):
    __tablename__ = 'audit_logs'

class Token(Base):
    __tablename__ = 'oauth2_tokens'
""",
    )
    monkeypatch.setattr(gate, "MODELS_DIR", tmp_path / "models")
    result = gate.check_soft_delete_models()
    assert result["status"] == gate.PASS
    assert sorted(result["missing_soft_delete"]) == []
    assert {entry["category"] for entry in result["inventory"]} == {
        "immutable_append_only_exception",
        "transient_operational_exception",
    }


def test_strict_mode_blocks_real_business_gap(tmp_path, monkeypatch):
    _write_model_tree(
        tmp_path,
        """
from .base import Base

class Patient(Base):
    __tablename__ = 'patients'
""",
    )
    monkeypatch.setattr(gate, "MODELS_DIR", tmp_path / "models")
    result = gate.check_soft_delete_models(strict=True)
    assert result["status"] == gate.FAIL
    assert result["missing_soft_delete"] == ["patients"]


def test_default_mode_surfaces_gap_as_warning(tmp_path, monkeypatch):
    _write_model_tree(
        tmp_path,
        """
from .base import Base

class Patient(Base):
    __tablename__ = 'patients'
""",
    )
    monkeypatch.setattr(gate, "MODELS_DIR", tmp_path / "models")
    result = gate.check_soft_delete_models()
    assert result["status"] == gate.WARNING
    assert result["missing_soft_delete"] == ["patients"]


def test_repository_inventory_has_no_unregistered_tables():
    result = gate.check_soft_delete_models()
    unregistered = [
        entry for entry in result["inventory"] if entry["category"] == "business_unregistered"
    ]
    assert unregistered == []
    assert all(entry["table"] in gate.PROTECTED_TABLES for entry in result["inventory"])
    assert result["status"] == gate.WARNING
    assert result["missing_soft_delete"]
