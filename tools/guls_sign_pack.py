#!/usr/bin/env python3
"""Sign a GULA language-pack directory without embedding private keys in output.

Usage:
  GULS_SIGNING_KEY_PATH=/secure/path/ed25519.pem \
  python tools/guls_sign_pack.py --language fa --version 1.0.0 \
    --source packs/fa --output dist/fa-1.0.0.zip --key-id gula-release-2026-01
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.localization.language_registry import LanguageRegistry
from app.localization.pack_builder import build_signed_pack
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def load_key(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("signing key must be Ed25519")
    return key


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--publisher", default="GULA National Language Board")
    parser.add_argument(
        "--approval-status",
        default="synthetic_test_only",
        choices=["approved", "synthetic_test_only"],
        help="Use approved only for a registry-approved, publishable language.",
    )
    args = parser.parse_args()

    import os

    private_key = load_key(Path(os.environ["GULS_SIGNING_KEY_PATH"]))
    registry = LanguageRegistry.load()
    files: dict[str, bytes] = {}
    for path in sorted(args.source.rglob("*")):
        if path.is_file():
            relative = path.relative_to(args.source).as_posix()
            files[relative] = path.read_bytes()
    if "manifest.json" in files:
        raise SystemExit("source must not contain manifest.json; it is generated and signed")
    pack = build_signed_pack(
        registry=registry,
        private_key=private_key,
        language_id=args.language,
        pack_version=args.version,
        signer_key_id=args.key_id,
        publisher=args.publisher,
        files=files,
        approval_status=args.approval_status,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(pack)
    # CLI result output is intentional; callers rely on this JSON line.
    print(json.dumps({"language_id": args.language, "pack_version": args.version, "bytes": len(pack)}))  # noqa: T201


if __name__ == "__main__":
    main()
