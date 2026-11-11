"""security.py: keypair generation + the sandbox allowlist constants."""
from __future__ import annotations

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from gula_edge_agent.security import ALLOWED_KINDS, MAX_PAYLOAD_BYTES, generate_keypair


def test_generate_keypair_returns_valid_2048_bit_rsa_pem():
    private_pem, public_pem = generate_keypair()

    private_key = serialization.load_pem_private_key(private_pem.encode(), password=None)
    assert isinstance(private_key, rsa.RSAPrivateKey)
    assert private_key.key_size == 2048

    public_key = serialization.load_pem_public_key(public_pem.encode())
    assert isinstance(public_key, rsa.RSAPublicKey)


def test_generate_keypair_produces_a_matching_pair_each_call():
    priv1, pub1 = generate_keypair()
    priv2, pub2 = generate_keypair()
    assert priv1 != priv2
    assert pub1 != pub2  # not reusing a fixed keypair across devices


def test_allowed_kinds_is_a_nonempty_frozenset_of_strings():
    assert isinstance(ALLOWED_KINDS, frozenset)
    assert ALLOWED_KINDS
    assert all(isinstance(k, str) for k in ALLOWED_KINDS)


def test_max_payload_bytes_is_a_sane_positive_ceiling():
    assert 0 < MAX_PAYLOAD_BYTES <= 10 * 1024 * 1024
