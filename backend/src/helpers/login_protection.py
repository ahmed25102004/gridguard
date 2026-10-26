
import hashlib
import os

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 15 * 60


def _key(kind: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"login-protection:{kind}:{digest}"


def is_login_blocked(email: str, client_ip: str) -> bool:
    """Check whether the account or IP has reached the attempt limit."""
    email_key = _key("email", email.strip().lower())
    ip_key = _key("ip", client_ip)

    email_count, ip_count = redis_client.mget(email_key, ip_key)

    return (
        int(email_count or 0) >= MAX_FAILED_ATTEMPTS
        or int(ip_count or 0) >= MAX_FAILED_ATTEMPTS
    )


def record_failed_login(email: str, client_ip: str) -> None:
    """Atomically increment failure counters and set their expiry."""
    script = """
    for i, key in ipairs(KEYS) do
        local count = redis.call('INCR', key)
        if count == 1 then
            redis.call('EXPIRE', key, ARGV[1])
        end
    end
    return 1
    """

    redis_client.eval(
        script,
        2,
        _key("email", email.strip().lower()),
        _key("ip", client_ip),
        LOCKOUT_WINDOW_SECONDS,
    )


def clear_account_login_failures(email: str) -> None:
    """Clear the account counter after successful authentication."""
    redis_client.delete(_key("email", email.strip().lower()))
