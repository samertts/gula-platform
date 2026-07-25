from __future__ import annotations

import base64
import logging
import math
import os
import secrets
import string
import uuid

logger = logging.getLogger("gula.security.modules.crypto.random")

_DEFAULT_PASSWORD_LENGTH = 24
_MIN_PASSWORD_LENGTH = 8
_MAX_PASSWORD_LENGTH = 128
_DEFAULT_PIN_LENGTH = 6


class SecureRandom:
    @staticmethod
    def bytes(count: int = 32) -> bytes:
        if count < 1:
            raise ValueError("Count must be positive")
        return os.urandom(count)

    @staticmethod
    def hex(count: int = 32) -> str:
        return secrets.token_hex(count)

    @staticmethod
    def base64(count: int = 32) -> str:
        return base64.urlsafe_b64encode(os.urandom(count)).rstrip(b"=").decode()

    @staticmethod
    def token_urlsafe(count: int = 32) -> str:
        return secrets.token_urlsafe(count)

    @staticmethod
    def int_below(upper_bound: int) -> int:
        return secrets.randbelow(upper_bound)

    @staticmethod
    def choice(sequence):
        return secrets.choice(sequence)

    @staticmethod
    def uuid4() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def generate_password(
        length: int = _DEFAULT_PASSWORD_LENGTH,
        use_lowercase: bool = True,
        use_uppercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True,
        exclude_chars: str = "",
        min_lowercase: int = 1,
        min_uppercase: int = 1,
        min_digits: int = 1,
        min_special: int = 1,
    ) -> str:
        if length < _MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password length must be at least {_MIN_PASSWORD_LENGTH}")
        if length > _MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password length must be at most {_MAX_PASSWORD_LENGTH}")

        char_sets: list[tuple[str, int]] = []
        if use_lowercase:
            chars = "".join(c for c in string.ascii_lowercase if c not in exclude_chars)
            if chars:
                char_sets.append((chars, min_lowercase))
        if use_uppercase:
            chars = "".join(c for c in string.ascii_uppercase if c not in exclude_chars)
            if chars:
                char_sets.append((chars, min_uppercase))
        if use_digits:
            chars = "".join(c for c in string.digits if c not in exclude_chars)
            if chars:
                char_sets.append((chars, min_digits))
        if use_special:
            special = "!@#$%^&*()_+-=[]{}|;:,.<>?/~"
            chars = "".join(c for c in special if c not in exclude_chars)
            if chars:
                char_sets.append((chars, min_special))

        if not char_sets:
            char_sets = [(string.ascii_letters + string.digits, 1)]

        total_min = sum(min_count for _, min_count in char_sets)
        if total_min > length:
            raise ValueError(
                f"Minimum character requirements ({total_min}) exceed password length ({length})"
            )

        password_chars: list[str] = []
        for charset, min_count in char_sets:
            for _ in range(min_count):
                password_chars.append(secrets.choice(charset))

        all_chars = "".join(cs for cs, _ in char_sets)
        remaining = length - len(password_chars)
        for _ in range(remaining):
            password_chars.append(secrets.choice(all_chars))

        secrets.SystemRandom().shuffle(password_chars)
        return "".join(password_chars)

    @staticmethod
    def generate_pin(length: int = _DEFAULT_PIN_LENGTH, avoid_sequential: bool = True) -> str:
        if length < 1 or length > 20:
            raise ValueError("PIN length must be between 1 and 20")

        if avoid_sequential:
            for _ in range(100):
                pin = "".join(str(secrets.randbelow(10)) for _ in range(length))
                if not SecureRandom._has_sequential_digits(pin) and not SecureRandom._has_repeating_digits(pin):
                    return pin
            return "".join(str(secrets.randbelow(10)) for _ in range(length))

        return "".join(str(secrets.randbelow(10)) for _ in range(length))

    @staticmethod
    def _has_sequential_digits(pin: str) -> bool:
        for i in range(len(pin) - 2):
            a, b, c = int(pin[i]), int(pin[i + 1]), int(pin[i + 2])
            if (b - a == 1 and c - b == 1) or (a - b == 1 and b - c == 1):
                return True
        return False

    @staticmethod
    def _has_repeating_digits(pin: str) -> bool:
        for i in range(len(pin) - 2):
            if pin[i] == pin[i + 1] == pin[i + 2]:
                return True
        return False

    @staticmethod
    def generate_api_key(prefix: str = "gula_") -> str:
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}{random_part}"

    @staticmethod
    def generate_otp_secret(length: int = 20) -> bytes:
        return os.urandom(length)

    @staticmethod
    def generate_salt(length: int = 16) -> bytes:
        return os.urandom(length)

    @staticmethod
    def estimate_entropy(value: str) -> float:
        if not value:
            return 0.0
        char_freq: dict[str, int] = {}
        for char in value:
            char_freq[char] = char_freq.get(char, 0) + 1
        length = len(value)
        entropy = 0.0
        for count in char_freq.values():
            prob = count / length
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return round(entropy * length, 2)

    @staticmethod
    def shuffle(data: list) -> list:
        result = list(data)
        secrets.SystemRandom().shuffle(result)
        return result
