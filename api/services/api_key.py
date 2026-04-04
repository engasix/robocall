import secrets
import hashlib


def generate() -> tuple[str, str]:
    """Generate a new API key.

    Returns (raw_key, hashed_key). Store only the hash — the raw key is shown
    once and cannot be recovered afterward.
    """
    raw = secrets.token_urlsafe(32)
    hashed = _hash(raw)
    return raw, hashed


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def verify(raw: str, stored_hash: str) -> bool:
    return _hash(raw) == stored_hash
