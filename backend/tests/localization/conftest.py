from __future__ import annotations

import base64
import io
import json
import zipfile
from pathlib import Path

import pytest
from app.localization.language_registry import LanguageRegistry
from app.localization.pack_builder import build_signed_pack, public_key_bytes
from app.localization.pack_manager import PackManager
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


@pytest.fixture()
def registry() -> LanguageRegistry:
    return LanguageRegistry.load()


@pytest.fixture()
def signing_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture()
def pack_manager(tmp_path: Path, registry: LanguageRegistry, signing_key: Ed25519PrivateKey) -> PackManager:
    return PackManager(
        tmp_path / "pack-state",
        registry,
        public_key=public_key_bytes(signing_key),
        allow_synthetic_packs=True,
    )


def synthetic_catalogs() -> dict[str, bytes]:
    return {
        "catalogs/common.json": json.dumps(
            {"ui.home": "Synthetic home", "ui.save": "Synthetic save"}, ensure_ascii=False
        ).encode("utf-8"),
        "terminology/clinical.json": json.dumps(
            {"concept": "SYNTHETIC", "original_value": "1.0", "unit": "mg"}
        ).encode("utf-8"),
        "metadata/README.md": b"Synthetic language pack for verification only. Not for clinical use.\n",
    }


def make_pack(
    registry: LanguageRegistry,
    signing_key: Ed25519PrivateKey,
    *,
    language_id: str = "fa",
    version: str = "1.0.0",
    files: dict[str, bytes] | None = None,
    approval_status: str = "synthetic_test_only",
) -> bytes:
    return build_signed_pack(
        registry=registry,
        private_key=signing_key,
        language_id=language_id,
        pack_version=version,
        signer_key_id="test-signer-01",
        publisher="GULA Synthetic Test Publisher",
        files=files or synthetic_catalogs(),
        approval_status=approval_status,
    )


def resign_pack(pack: bytes, key: Ed25519PrivateKey, mutate: object) -> bytes:
    """Rewrite and re-sign the manifest for negative governance tests."""
    from app.localization.pack_schema import LanguagePackManifest

    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(pack)) as source, zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == "manifest.json":
                payload = json.loads(data)
                mutate(payload)
                manifest = LanguagePackManifest.model_validate(payload)
                manifest.signature = "AA=="
                payload = json.loads(manifest.model_dump_json())
                payload["signature"] = base64.b64encode(key.sign(manifest.signing_payload())).decode("ascii")
                data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            target.writestr(info.filename, data)
    return buffer.getvalue()


def replace_zip_member(pack: bytes, member_name: str, replacement: bytes) -> bytes:
    """Rewrite one archive member while preserving all other bytes verbatim."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(pack)) as source, zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            data = replacement if info.filename == member_name else source.read(info.filename)
            target.writestr(info.filename, data)
    return buffer.getvalue()
