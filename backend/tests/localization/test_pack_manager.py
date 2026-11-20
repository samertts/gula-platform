from __future__ import annotations

import base64
import io
import json
import zipfile
from datetime import UTC, datetime, timezone

import pytest
from app.localization.clinical import PackGovernanceError
from app.localization.pack_builder import build_signed_pack, public_key_bytes
from app.localization.pack_manager import (
    ApprovalError,
    CompatibilityError,
    DownloadIncompleteError,
    IntegrityError,
    InvalidStateTransition,
    PackError,
    SignatureVerificationError,
    UnsafeArchiveError,
)
from app.localization.pack_schema import ApprovalRecord
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .conftest import make_pack, replace_zip_member, resign_pack


def test_install_success_sets_ready_and_loads_catalog(registry, signing_key, pack_manager):
    pack = make_pack(registry, signing_key)
    manifest = pack_manager.install("fa", pack)
    assert manifest.pack_version == "1.0.0"
    assert pack_manager.state("fa") == "READY"
    assert pack_manager.active_version("fa") == "1.0.0"
    assert pack_manager.active_catalog("fa", "common")["ui.home"] == "Synthetic home"


def test_unsigned_or_wrong_key_pack_is_rejected(registry, pack_manager):
    other_key = Ed25519PrivateKey.generate()
    pack = make_pack(registry, other_key)
    with pytest.raises(SignatureVerificationError):
        pack_manager.install("fa", pack)


def test_modified_content_after_signing_is_rejected(registry, signing_key, pack_manager):
    pack = make_pack(registry, signing_key)
    tampered = replace_zip_member(pack, "catalogs/common.json", b'{"ui.home":"Tampered"}')
    with pytest.raises(IntegrityError):
        pack_manager.install("fa", tampered)


def test_invalid_manifest_is_rejected(registry, signing_key, pack_manager):
    pack = make_pack(registry, signing_key)
    broken = replace_zip_member(pack, "manifest.json", b"{not-json")
    with pytest.raises(IntegrityError):
        pack_manager.install("fa", broken)


def test_path_traversal_is_rejected(registry, signing_key, pack_manager):
    files = {"catalogs/common.json": b"{}", "catalogs/../../evil.json": b"{}"}
    with pytest.raises(UnsafeArchiveError):
        build_signed_pack(
            registry=registry,
            private_key=signing_key,
            language_id="fa",
            pack_version="1.0.0",
            signer_key_id="test-signer-01",
            publisher="Synthetic",
            files=files,
        )


def test_executable_file_is_rejected(registry, signing_key, pack_manager):
    files = {"catalogs/common.json": b"{}", "fonts/payload.exe": b"MZ"}
    with pytest.raises(UnsafeArchiveError):
        build_signed_pack(
            registry=registry,
            private_key=signing_key,
            language_id="fa",
            pack_version="1.0.0",
            signer_key_id="test-signer-01",
            publisher="Synthetic",
            files=files,
        )


def test_oversized_file_is_rejected(registry, signing_key, pack_manager):
    files = {"catalogs/common.json": b"x" * (10 * 1024 * 1024 + 1)}
    with pytest.raises(UnsafeArchiveError):
        build_signed_pack(
            registry=registry,
            private_key=signing_key,
            language_id="fa",
            pack_version="1.0.0",
            signer_key_id="test-signer-01",
            publisher="Synthetic",
            files=files,
        )


def test_unapproved_pack_is_rejected_in_production_mode(registry, signing_key, tmp_path):
    from app.localization.pack_manager import PackManager

    production_manager = PackManager(
        tmp_path / "production-state",
        registry,
        public_key=public_key_bytes(signing_key),
        allow_synthetic_packs=False,
    )
    with pytest.raises(ApprovalError):
        production_manager.install("fa", make_pack(registry, signing_key))


def test_engine_compatibility_is_enforced(registry, signing_key, pack_manager):
    pack = resign_pack(
        make_pack(registry, signing_key),
        signing_key,
        lambda payload: payload.update(minimum_engine_version="99.0.0"),
    )
    with pytest.raises(CompatibilityError):
        pack_manager.verify(pack, "fa")


def test_update_and_rollback_preserve_previous_pack(registry, signing_key, pack_manager):
    pack_manager.install("fa", make_pack(registry, signing_key, version="1.0.0"))
    assert pack_manager.active_version("fa") == "1.0.0"
    pack_manager.install("fa", make_pack(registry, signing_key, version="1.1.0"))
    assert pack_manager.active_version("fa") == "1.1.0"
    assert pack_manager._language_state("fa")["previous_version"] == "1.0.0"

    with pytest.raises(SignatureVerificationError):
        bad_key = Ed25519PrivateKey.generate()
        pack_manager.install("fa", make_pack(registry, bad_key, version="1.2.0"))
    assert pack_manager.active_version("fa") == "1.1.0"
    assert pack_manager.state("fa") == "READY"


def test_downgrade_is_rejected(registry, signing_key, pack_manager):
    pack_manager.install("fa", make_pack(registry, signing_key, version="2.0.0"))
    with pytest.raises(CompatibilityError):
        pack_manager.install("fa", make_pack(registry, signing_key, version="1.0.0"))


def test_duplicate_install_does_not_reinstall(registry, signing_key, pack_manager):
    pack = make_pack(registry, signing_key)
    pack_manager.install("fa", pack)
    pack_manager.install("fa", pack)
    assert pack_manager.active_version("fa") == "1.0.0"


def test_resumable_download_and_concurrent_guard(registry, signing_key, pack_manager):
    pack = make_pack(registry, signing_key)
    session, chunk = pack_manager.download("fa", expected_size=len(pack), transport=lambda _id, _off: pack[:10], resume_from=0, download_id="d1")
    assert session.status == "DOWNLOADING"
    assert session.last_error == "partial_download_resumable"
    with pytest.raises(PackError):
        pack_manager.download("fa", expected_size=len(pack), transport=lambda _id, _off: b"", resume_from=0, download_id="d2")
    resumed, remainder = pack_manager.download("fa", expected_size=len(pack), transport=lambda _id, _off: pack[10:], resume_from=10, download_id="d1")
    assert resumed.downloaded_bytes == len(pack)
    assert chunk + remainder == pack


def test_download_size_mismatch_fails(registry, signing_key, pack_manager):
    with pytest.raises(DownloadIncompleteError):
        pack_manager.download(
            "fa",
            expected_size=3,
            transport=lambda _id, _off: b"123456",
            resume_from=0,
            download_id="bad",
        )


def test_explicit_state_transition_is_validated(pack_manager):
    with pytest.raises(InvalidStateTransition):
        pack_manager.transition("fa", "READY")


def test_pending_language_cannot_be_downloaded(pack_manager):
    with pytest.raises(ApprovalError):
        pack_manager.download("PENDING_SYRIAC", expected_size=1, transport=lambda *_: b"x", resume_from=0, download_id="x")


def test_l4_approval_requires_clinical_reviewer():
    with pytest.raises(ValueError):
        ApprovalRecord(
            translation_key="clinical.allergy",
            content_class="L4",
            source_text="Penicillin allergy",
            translated_text="Synthetic translation",
            translator="translator-a",
            linguistic_reviewer="reviewer-b",
            clinical_reviewer=None,
            approved_at=datetime.now(UTC),
            package_version="1.0.0",
            change_reason="initial",
        )


def test_approved_pack_for_blocked_language_is_rejected(registry, signing_key, pack_manager):
    pack = resign_pack(make_pack(registry, signing_key), signing_key, lambda payload: payload.update(approval_status="approved"))
    with pytest.raises(ApprovalError):
        pack_manager.install("fa", pack)


def test_clinical_catalog_cannot_be_signed_without_clinical_approval(registry, signing_key):
    with pytest.raises(PackGovernanceError):
        build_signed_pack(
            registry=registry,
            private_key=signing_key,
            language_id="ar",
            pack_version="1.0.0",
            signer_key_id="test-signer-01",
            publisher="Synthetic",
            files={"catalogs/clinical.json": b'{"clinical.allergy": "Synthetic"}'},
        )


def test_expected_hash_mismatch_is_rejected(registry, signing_key, pack_manager):
    with pytest.raises(IntegrityError):
        pack_manager.install("fa", make_pack(registry, signing_key), expected_hash="0" * 64)


def test_install_recovers_from_stale_target_directory(registry, signing_key, pack_manager):
    pack_manager.install("fa", make_pack(registry, signing_key, version="1.0.0"))
    stale = pack_manager.root / "packs" / "fa" / "2.0.0"
    stale.mkdir(parents=True)
    (stale / "partial.json").write_text("interrupted", encoding="utf-8")

    pack_manager.install("fa", make_pack(registry, signing_key, version="2.0.0"))

    assert pack_manager.active_version("fa") == "2.0.0"
    assert not (stale / "partial.json").exists()
    assert pack_manager.active_catalog("fa", "common")["ui.home"] == "Synthetic home"


def test_malformed_public_key_does_not_break_startup(registry, signing_key, tmp_path, monkeypatch):
    from app.localization.pack_manager import PackManager

    monkeypatch.setenv("GULS_PACK_PUBLIC_KEY_B64", "!!!not-base64!!!")
    manager = PackManager(tmp_path / "bad-key-state", registry, allow_synthetic_packs=True)
    with pytest.raises(SignatureVerificationError, match="invalid"):
        manager.verify(make_pack(registry, signing_key), "fa")
