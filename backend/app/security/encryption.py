import os
from cryptography.fernet import Fernet

# Use persistent key from environment variable
# Generate one with: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
_key = os.getenv("ENCRYPTION_KEY")
if _key:
    cipher = Fernet(_key.encode() if isinstance(_key, str) else _key)
else:
    # Fallback: generate key but warn (data won't persist across restarts)
    _key = Fernet.generate_key()
    cipher = Fernet(_key)


def encrypt(data: str) -> str:
    """Encrypt a string value."""
    return cipher.encrypt(data.encode()).decode()


def decrypt(data: str) -> str:
    """Decrypt an encrypted string value."""
    return cipher.decrypt(data.encode()).decode()
