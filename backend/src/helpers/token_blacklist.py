import hashlib
import os
import time

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def _get_blacklist_key(token: str) -> str:
    """Return a SHA-256-based Redis key for a JWT."""
    if not token:
        raise ValueError("Token must not be empty.")

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"blacklist:{token_hash}"


def blacklist_token(token: str, expires_at: int) -> None:
    """Revoke a JWT until its expiration timestamp (Unix seconds)."""
    if not isinstance(expires_at, (int, float)) or isinstance(expires_at, bool):
        raise ValueError("expires_at must be a Unix timestamp.")

    ttl = int(expires_at - time.time())

    if ttl <= 0:
        return

    redis_client.setex(
        _get_blacklist_key(token),
        ttl,
        "revoked",
    )


def is_token_blacklisted(token: str) -> bool:
    """Check whether a JWT has been revoked."""
    return bool(redis_client.exists(_get_blacklist_key(token)))
