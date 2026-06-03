import base64
import hashlib

from cryptography.fernet import Fernet

from api.config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    key_material = settings.api_key_secret or settings.secret_key
    if not key_material:
        raise RuntimeError("Encryption key is not configured")
    digest = hashlib.sha256(key_material.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_text(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_text(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
