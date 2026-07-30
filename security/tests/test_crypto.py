from __future__ import annotations

import os

import pytest

from security.modules.crypto.key_rotation import KeyRotationManager
from security.modules.crypto.models import (
    EncryptedData,
    EncryptionAlgorithm,
    HashAlgorithm,
    HashResult,
    KeyPurpose,
    SignatureAlgorithm,
)
from security.modules.crypto.signing import ECDSA256Signer, Ed25519Signer, HMACSigner


class TestAES256GCM:
    def test_aes256_gcm_encrypt_decrypt(self, crypto_aes256_gcm, aes_key):
        plaintext = b"test data for encryption"
        encrypted = crypto_aes256_gcm.encrypt(plaintext, aes_key)
        assert encrypted != plaintext
        decrypted = crypto_aes256_gcm.decrypt(encrypted, aes_key)
        assert decrypted == plaintext

    def test_aes256_gcm_authentication_tag(self, crypto_aes256_gcm, aes_key):
        plaintext = b"sensitive patient data"
        encrypted = crypto_aes256_gcm.encrypt(plaintext, aes_key)
        assert len(encrypted) > len(plaintext) + 12
        tag = encrypted[-16:]
        assert len(tag) == 16

    def test_aes256_gcm_wrong_key(self, crypto_aes256_gcm, aes_key):
        plaintext = b"test data"
        encrypted = crypto_aes256_gcm.encrypt(plaintext, aes_key)
        wrong_key = os.urandom(32)
        with pytest.raises(Exception):
            crypto_aes256_gcm.decrypt(encrypted, wrong_key)

    def test_aes256_gcm_empty_data(self, crypto_aes256_gcm, aes_key):
        with pytest.raises(ValueError):
            crypto_aes256_gcm.encrypt(b"", aes_key)

    def test_aes256_gcm_with_aad(self, crypto_aes256_gcm, aes_key):
        plaintext = b"data with aad"
        aad = b"additional authenticated data"
        encrypted = crypto_aes256_gcm.encrypt_with_associated_data(plaintext, aes_key, aad)
        decrypted = crypto_aes256_gcm.decrypt_with_associated_data(encrypted, aes_key, aad)
        assert decrypted == plaintext

    def test_aes256_gcm_wrong_aad(self, crypto_aes256_gcm, aes_key):
        plaintext = b"data with aad"
        encrypted = crypto_aes256_gcm.encrypt_with_associated_data(plaintext, aes_key, b"correct aad")
        with pytest.raises(Exception):
            crypto_aes256_gcm.decrypt_with_associated_data(encrypted, aes_key, b"wrong aad")

    def test_aes256_gcm_key_generation(self, crypto_aes256_gcm):
        key = crypto_aes256_gcm.generate_key()
        assert len(key) == 32

    def test_aes256_gcm_key_derivation(self, crypto_aes256_gcm):
        password = b"strong_password"
        salt = os.urandom(16)
        key = crypto_aes256_gcm.derive_key(password, salt)
        assert len(key) == 32
        key2 = crypto_aes256_gcm.derive_key(password, salt)
        assert key == key2

    def test_aes256_gcm_large_data(self, crypto_aes256_gcm, aes_key):
        plaintext = os.urandom(1024 * 1024)
        encrypted = crypto_aes256_gcm.encrypt(plaintext, aes_key)
        decrypted = crypto_aes256_gcm.decrypt(encrypted, aes_key)
        assert decrypted == plaintext


class TestAES256CBCWithHMAC:
    def test_aes256_cbc_hmac_encrypt_then_mac(self, crypto_aes256_cbc_hmac, aes_cbc_hmac_key):
        plaintext = b"test data for CBC+HMAC"
        encrypted = crypto_aes256_cbc_hmac.encrypt(plaintext, aes_cbc_hmac_key)
        assert encrypted != plaintext
        decrypted = crypto_aes256_cbc_hmac.decrypt(encrypted, aes_cbc_hmac_key)
        assert decrypted == plaintext

    def test_aes256_cbc_hmac_tamper_detection(self, crypto_aes256_cbc_hmac, aes_cbc_hmac_key):
        plaintext = b"sensitive data"
        encrypted = crypto_aes256_cbc_hmac.encrypt(plaintext, aes_cbc_hmac_key)
        tampered = bytearray(encrypted)
        tampered[-1] ^= 0xFF
        with pytest.raises(ValueError, match="HMAC verification failed"):
            crypto_aes256_cbc_hmac.decrypt(bytes(tampered), aes_cbc_hmac_key)

    def test_aes256_cbc_hmac_key_length(self, crypto_aes256_cbc_hmac):
        key = crypto_aes256_cbc_hmac.generate_key()
        assert len(key) == 64

    def test_aes256_cbc_hmac_empty_data(self, crypto_aes256_cbc_hmac, aes_cbc_hmac_key):
        with pytest.raises(ValueError):
            crypto_aes256_cbc_hmac.encrypt(b"", aes_cbc_hmac_key)

    def test_aes256_cbc_hmac_padding(self, crypto_aes256_cbc_hmac):
        key = crypto_aes256_cbc_hmac.generate_key()
        padded = crypto_aes256_cbc_hmac.encrypt(b"short", key)
        unpadded = crypto_aes256_cbc_hmac.decrypt(padded, key)
        assert unpadded == b"short"


class TestArgon2id:
    def test_argon2id_hashing_and_verification(self, crypto_argon2id):
        password = b"correct horse battery staple"
        hashed = crypto_argon2id.hash(password)
        assert crypto_argon2id.verify(password, hashed) is True

    def test_argon2id_wrong_password(self, crypto_argon2id):
        password = b"correct password"
        wrong = b"wrong password"
        hashed = crypto_argon2id.hash(password)
        assert crypto_argon2id.verify(wrong, hashed) is False

    def test_argon2id_empty_data(self, crypto_argon2id):
        with pytest.raises(ValueError):
            crypto_argon2id.hash(b"")

    def test_argon2id_needs_rehash(self, crypto_argon2id):
        hashed = crypto_argon2id.hash(b"test password")
        assert crypto_argon2id.needs_rehash(hashed) is False


class TestEd25519:
    def test_ed25519_signing_and_verification(self, crypto_ed25519_signer):
        message = b"critical system message"
        signature = crypto_ed25519_signer.sign(message)
        assert crypto_ed25519_signer.verify(message, signature) is True

    def test_ed25519_verify_wrong_message(self, crypto_ed25519_signer):
        message = b"original message"
        signature = crypto_ed25519_signer.sign(message)
        assert crypto_ed25519_signer.verify(b"tampered message", signature) is False

    def test_ed25519_key_pair_generation(self):
        priv, pub = Ed25519Signer.generate_key_pair()
        assert len(priv) == 32
        assert len(pub) == 32


class TestECDSA:
    def test_ecdsa_signing_and_verification(self, crypto_ecdsa_signer):
        message = b"ecdsa test message"
        signature = crypto_ecdsa_signer.sign(message)
        assert crypto_ecdsa_signer.verify(message, signature) is True

    def test_ecdsa_verify_wrong_signature(self, crypto_ecdsa_signer):
        message = b"test message"
        signature = crypto_ecdsa_signer.sign(message)
        assert crypto_ecdsa_signer.verify(b"different", signature) is False

    def test_ecdsa_key_pair_generation(self):
        priv, pub = ECDSA256Signer.generate_key_pair()
        assert len(priv) == 32


class TestHMAC:
    def test_hmac_signing(self, crypto_hmac_signer, hmac_key):
        message = b"authenticated message"
        signature = crypto_hmac_signer.sign(message, hmac_key)
        assert crypto_hmac_signer.verify(message, signature, hmac_key) is True

    def test_hmac_wrong_key(self, crypto_hmac_signer, hmac_key):
        message = b"test"
        signature = crypto_hmac_signer.sign(message, hmac_key)
        wrong_key = os.urandom(32)
        assert crypto_hmac_signer.verify(message, signature, wrong_key) is False

    def test_hmac_empty_key(self, crypto_hmac_signer):
        with pytest.raises(ValueError):
            crypto_hmac_signer.sign(b"data", b"")

    def test_hmac_hex_format(self, crypto_hmac_signer, hmac_key):
        sig_hex = crypto_hmac_signer.sign_hex(b"data", hmac_key)
        assert crypto_hmac_signer.verify_hex(b"data", sig_hex, hmac_key) is True


class TestHashing:
    def test_sha256_hashing(self, crypto_sha256):
        data = b"test data for hashing"
        digest = crypto_sha256.hash(data)
        assert len(digest) == 32
        assert crypto_sha256.verify(data, digest) is True

    def test_sha512_hashing(self, crypto_sha512):
        data = b"test data for sha512"
        digest = crypto_sha512.hash(data)
        assert len(digest) == 64
        assert crypto_sha512.verify(data, digest) is True

    def test_sha256_salted_hash(self, crypto_sha256):
        data = b"sensitive data"
        salted = crypto_sha256.hash_salted(data)
        assert crypto_sha256.verify_salted(data, salted) is True

    def test_sha256_hex(self, crypto_sha256):
        hex_val = crypto_sha256.hash_hex(b"data")
        assert isinstance(hex_val, str)
        assert len(hex_val) == 64

    def test_sha256_stream(self, crypto_sha256):
        import io
        stream = io.BytesIO(b"stream data for hashing")
        digest = crypto_sha256.hash_stream(stream)
        assert len(digest) == 32

    def test_sha256_hkdf(self, crypto_sha256):
        prk = crypto_sha256.hkdf_extract(b"salt", b"ikm material")
        expanded = crypto_sha256.hkdf_expand(prk, 48, b"context")
        assert len(expanded) == 48


class TestSecureRandom:
    def test_secure_random_generation(self, crypto_secure_random):
        rand_bytes = crypto_secure_random.bytes(32)
        assert len(rand_bytes) == 32

    def test_password_generation(self, crypto_secure_random):
        password = crypto_secure_random.generate_password()
        assert len(password) >= 24
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~" for c in password)

    def test_pin_generation(self, crypto_secure_random):
        pin = crypto_secure_random.generate_pin()
        assert len(pin) == 6
        assert pin.isdigit()

    def test_api_key_generation(self, crypto_secure_random):
        key = crypto_secure_random.generate_api_key()
        assert key.startswith("gula_")
        assert len(key) > 32

    def test_entropy_estimation(self, crypto_secure_random):
        entropy = crypto_secure_random.estimate_entropy("".join(chr(i) for i in range(256)))
        assert entropy > 100

    def test_token_urlsafe(self, crypto_secure_random):
        token = crypto_secure_random.token_urlsafe(32)
        assert len(token) > 32

    def test_uuid4(self, crypto_secure_random):
        uuid = crypto_secure_random.uuid4()
        assert len(uuid) == 36

    def test_choice(self, crypto_secure_random):
        seq = [1, 2, 3, 4, 5]
        chosen = crypto_secure_random.choice(seq)
        assert chosen in seq

    def test_shuffle(self, crypto_secure_random):
        data = [1, 2, 3, 4, 5]
        shuffled = crypto_secure_random.shuffle(data)
        assert sorted(shuffled) == sorted(data)

    def test_salt_generation(self, crypto_secure_random):
        salt = crypto_secure_random.generate_salt()
        assert len(salt) == 16


class TestFieldEncryption:
    def test_field_encryption_deterministic(self, field_encryptor):
        encrypted1 = field_encryptor.encrypt_field("patient-123", "nin", "patients", deterministic=True)
        encrypted2 = field_encryptor.encrypt_field("patient-123", "nin", "patients", deterministic=True)
        assert encrypted1 == encrypted2
        decrypted = field_encryptor.decrypt_field(encrypted1, "nin", "patients")
        assert decrypted == "patient-123"

    def test_field_encryption_probabilistic(self, field_encryptor):
        encrypted1 = field_encryptor.encrypt_field("sensitive-value", "email", "users")
        encrypted2 = field_encryptor.encrypt_field("sensitive-value", "email", "users")
        assert encrypted1 != encrypted2

    def test_field_encrypt_int(self, field_encryptor):
        enc = field_encryptor.encrypt_int(12345, "age", "patients")
        dec = field_encryptor.decrypt_int(enc, "age", "patients")
        assert dec == 12345

    def test_field_encrypt_float(self, field_encryptor):
        enc = field_encryptor.encrypt_float(98.6, "temperature", "observations")
        dec = field_encryptor.decrypt_float(enc, "temperature", "observations")
        assert dec == pytest.approx(98.6)

    def test_field_encrypt_bool(self, field_encryptor):
        enc = field_encryptor.encrypt_bool(True, "is_active", "users")
        dec = field_encryptor.decrypt_bool(enc, "is_active", "users")
        assert dec is True

    def test_field_encrypt_json(self, field_encryptor):
        data = {"name": "test", "value": 42}
        enc = field_encryptor.encrypt_json(data, "metadata", "records")
        dec = field_encryptor.decrypt_json(enc, "metadata", "records")
        assert dec == data

    def test_blind_index(self, field_encryptor):
        idx1 = field_encryptor.generate_blind_index("patient@example.com", "email", "patients")
        idx2 = field_encryptor.generate_blind_index("patient@example.com", "email", "patients")
        assert idx1 == idx2
        assert len(idx1) == 32

    def test_encrypted_with_index(self, field_encryptor):
        enc, idx = field_encryptor.create_encrypted_with_index("value", "field", "table")
        assert enc.startswith("enc:")
        assert len(idx) == 32


class TestPHIEncryption:
    def test_phi_encryption_key_hierarchy(self, phi_encryptor):
        encrypted = phi_encryptor.encrypt_phi_field("patient-name", "pat-001", "patients", "name")
        assert encrypted.startswith("phi:")
        decrypted = phi_encryptor.decrypt_phi_field(encrypted, "pat-001", "patients", "name")
        assert decrypted == "patient-name"

    def test_phi_encryption_different_patients(self, phi_encryptor):
        enc1 = phi_encryptor.encrypt_phi_field("John Doe", "pat-001", "patients", "name")
        enc2 = phi_encryptor.encrypt_phi_field("John Doe", "pat-002", "patients", "name")
        assert enc1 != enc2

    def test_phi_encryption_consent_token(self, phi_encryptor):
        token = phi_encryptor.generate_consent_token("pat-001")
        encrypted = phi_encryptor.encrypt_phi_field("data", "pat-001", "records", "phi", consent_token=token)
        decrypted = phi_encryptor.decrypt_phi_field(encrypted, "pat-001", "records", "phi")
        assert decrypted == "data"

    def test_phi_encryption_wrong_consent(self, phi_encryptor):
        with pytest.raises(PermissionError):
            phi_encryptor.encrypt_phi_field("data", "pat-001", "records", "phi", consent_token="invalid")

    def test_phi_break_glass_access(self, phi_encryptor):
        encrypted = phi_encryptor.encrypt_phi_field("secret", "pat-001", "patients", "phi_field")
        emergency_key = os.urandom(32)
        phi_encryptor.enable_break_glass(emergency_key)
        decrypted = phi_encryptor.decrypt_phi_field(encrypted, "pat-001", "patients", "phi_field", break_glass=True, break_glass_reason="emergency")
        assert decrypted == "secret"

    def test_phi_re_encrypt(self, phi_encryptor):
        old_key = phi_encryptor._master_key
        new_key = os.urandom(32)
        encrypted = phi_encryptor.encrypt_phi_field("data", "pat-001", "t", "c")
        phi_encryptor.rotate_master_key(new_key)
        re_encrypted = phi_encryptor.re_encrypt_patient_data("pat-001", "t", {"c": encrypted}, old_key)
        assert "c" in re_encrypted

    def test_phi_audit_log(self, phi_encryptor):
        phi_encryptor.encrypt_phi_field("data1", "pat-001", "t", "c1")
        phi_encryptor.encrypt_phi_field("data2", "pat-001", "t", "c2")
        log = phi_encryptor.get_audit_log()
        assert len(log) >= 2
        assert all("action" in entry for entry in log)


class TestKeyRotation:
    def test_key_rotation(self, key_rotation_manager):
        key_rotation_manager.add_key("test-key", os.urandom(32))
        old_key_id = key_rotation_manager.active_key_id
        new_key_id = key_rotation_manager.rotate()
        assert new_key_id != old_key_id
        assert key_rotation_manager.active_key_id == new_key_id

    def test_key_rotation_metadata(self, key_rotation_manager):
        key_rotation_manager.add_key("key-1", os.urandom(32))
        key_rotation_manager.rotate()
        history = key_rotation_manager.get_rotation_history()
        assert len(history) >= 1

    def test_emergency_rotation(self, key_rotation_manager):
        key_rotation_manager.add_key("key-1", os.urandom(32))
        new_key_id = key_rotation_manager.emergency_rotation()
        assert new_key_id is not None

    def test_key_backup_and_restore(self, key_rotation_manager):
        key_rotation_manager.add_key("backup-key", os.urandom(32))
        passphrase = b"test-passphrase-32-bytes-long!!!!!"
        backup = key_rotation_manager.backup_keys(passphrase)
        assert len(backup) > 0
        new_mgr = KeyRotationManager()
        new_mgr.restore_keys(backup, passphrase)
        assert new_mgr.get_current_key() == key_rotation_manager.get_current_key()

    def test_grace_period(self, key_rotation_manager):
        key_rotation_manager.add_key("key-1", os.urandom(32))
        key_rotation_manager.rotate()
        assert key_rotation_manager.is_key_in_grace_period("key-1") is True

    def test_list_keys(self, key_rotation_manager):
        key_rotation_manager.add_key("key-1", os.urandom(32))
        key_rotation_manager.add_key("key-2", os.urandom(32))
        keys = key_rotation_manager.list_keys()
        assert len(keys) >= 2

