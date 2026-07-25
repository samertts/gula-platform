from __future__ import annotations

import os

import pytest


class TestAESBenchmark:
    def bench_aes_encrypt(self, benchmark, crypto_fixtures):
        aes = crypto_fixtures["aes"]
        data = os.urandom(1024 * 1024)
        result = benchmark(aes.encrypt, data)
        assert result is not None

    def bench_aes_decrypt(self, benchmark, crypto_fixtures):
        aes = crypto_fixtures["aes"]
        data = os.urandom(1024 * 1024)
        ciphertext, tag, nonce = aes.encrypt(data)
        result = benchmark(aes.decrypt, ciphertext, tag, nonce)
        assert result == data

    def bench_aes_small_data(self, benchmark, crypto_fixtures):
        aes = crypto_fixtures["aes"]
        data = b"hello world"
        result = benchmark(aes.encrypt, data)
        assert result is not None

    def bench_aes_large_data(self, benchmark, crypto_fixtures):
        aes = crypto_fixtures["aes"]
        data = os.urandom(10 * 1024 * 1024)
        result = benchmark(aes.encrypt, data)
        assert result is not None


class TestArgon2Benchmark:
    def bench_argon2_hash(self, benchmark, crypto_fixtures):
        argon2 = crypto_fixtures["argon2"]
        password = "test_password_123"
        result = benchmark(argon2.hash, password)
        assert result is not None

    def bench_argon2_verify(self, benchmark, crypto_fixtures):
        argon2 = crypto_fixtures["argon2"]
        password = "test_password_123"
        hashed = argon2.hash(password)
        result = benchmark(argon2.verify, password, hashed)
        assert result is True

    def bench_argon2_wrong_password(self, benchmark, crypto_fixtures):
        argon2 = crypto_fixtures["argon2"]
        password = "test_password_123"
        hashed = argon2.hash(password)
        result = benchmark(argon2.verify, "wrong_password", hashed)
        assert result is False


class TestEd25519Benchmark:
    def bench_ed25519_sign(self, benchmark, crypto_fixtures):
        ed25519 = crypto_fixtures["ed25519"]
        message = b"test message for signing"
        private_key = ed25519.generate_private_key()
        result = benchmark(ed25519.sign, message, private_key)
        assert result is not None

    def bench_ed25519_verify(self, benchmark, crypto_fixtures):
        ed25519 = crypto_fixtures["ed25519"]
        message = b"test message for signing"
        private_key = ed25519.generate_private_key()
        public_key = ed25519.derive_public_key(private_key)
        signature = ed25519.sign(message, private_key)
        result = benchmark(ed25519.verify, message, signature, public_key)
        assert result is True


class TestHMACBenchmark:
    def bench_hmac_generate(self, benchmark, crypto_fixtures):
        hmac = crypto_fixtures["hmac"]
        key = os.urandom(32)
        message = b"test message for hmac"
        result = benchmark(hmac.generate, key, message)
        assert result is not None

    def bench_hmac_verify(self, benchmark, crypto_fixtures):
        hmac = crypto_fixtures["hmac"]
        key = os.urandom(32)
        message = b"test message for hmac"
        tag = hmac.generate(key, message)
        result = benchmark(hmac.verify, key, message, tag)
        assert result is True


class TestSHABenchmark:
    def bench_sha256_hash(self, benchmark, crypto_fixtures):
        sha = crypto_fixtures["sha"]
        data = os.urandom(1024 * 1024)
        result = benchmark(sha.hash, data)
        assert result is not None

    def bench_sha256_small(self, benchmark, crypto_fixtures):
        sha = crypto_fixtures["sha"]
        data = b"small data"
        result = benchmark(sha.hash, data)
        assert result is not None


class TestSecureRandomBenchmark:
    def bench_random_bytes(self, benchmark, crypto_fixtures):
        rand = crypto_fixtures["random"]
        result = benchmark(rand.generate, 1024)
        assert len(result) == 1024

    def bench_random_string(self, benchmark, crypto_fixtures):
        rand = crypto_fixtures["random"]
        result = benchmark(rand.generate_string, 64)
        assert len(result) == 64
