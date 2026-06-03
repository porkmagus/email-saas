import hashlib
import hmac

from api.config import get_settings


def _api_key_secret() -> str:
    settings = get_settings()
    secret = settings.api_key_secret or settings.secret_key
    if not secret:
        raise RuntimeError("API key secret is not configured")
    return secret


def hash_api_key(raw: str) -> str:
    secret = _api_key_secret()
    return hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()


def verify_api_key(raw: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw), hashed)
