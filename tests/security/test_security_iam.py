
import bcrypt
import pytest
from fastapi import HTTPException

from backend.src.helpers.password_policy import validate_password_strength
from backend.src.helpers import token_blacklist, login_protection
from backend.src.middleware.timing_defense import verify_password_timing_safe


# --------------------------------------------------
# Password policy
# --------------------------------------------------

def test_valid_password():
    assert validate_password_strength("GridGuard@2026") is True


def test_valid_password_exactly_8_characters():
    assert validate_password_strength("Grid@123") is True


def test_short_password():
    with pytest.raises(HTTPException) as exc_info:
        validate_password_strength("Short1@")

    assert exc_info.value.status_code == 400
    assert "at least 8 characters long" in exc_info.value.detail


def test_missing_uppercase_password():
    with pytest.raises(HTTPException) as exc_info:
        validate_password_strength("gridguard@2026")

    assert exc_info.value.status_code == 400
    assert "uppercase letter" in exc_info.value.detail


def test_missing_lowercase_password():
    with pytest.raises(HTTPException) as exc_info:
        validate_password_strength("GRIDGUARD@2026")

    assert exc_info.value.status_code == 400
    assert "lowercase letter" in exc_info.value.detail


def test_missing_digit_password():
    with pytest.raises(HTTPException) as exc_info:
        validate_password_strength("GridGuard@Pass")

    assert exc_info.value.status_code == 400
    assert "digit" in exc_info.value.detail


def test_missing_special_char_password():
    with pytest.raises(HTTPException) as exc_info:
        validate_password_strength("GridGuard2026")

    assert exc_info.value.status_code == 400
    assert "special character" in exc_info.value.detail


# --------------------------------------------------
# Timing defense / bcrypt verification
# --------------------------------------------------

@pytest.fixture
def valid_bcrypt_hash():
    # Low rounds keep the test fast; production must use cost >= 12.
    return bcrypt.hashpw(
        b"GridGuard@2026",
        bcrypt.gensalt(rounds=4),
    ).decode("utf-8")


def test_timing_defense_accepts_correct_password(valid_bcrypt_hash):
    assert verify_password_timing_safe(
        "GridGuard@2026",
        valid_bcrypt_hash,
    ) is True


def test_timing_defense_rejects_wrong_password(valid_bcrypt_hash):
    assert verify_password_timing_safe(
        "WrongPassword@2026",
        valid_bcrypt_hash,
    ) is False


def test_timing_defense_rejects_invalid_hash():
    assert verify_password_timing_safe(
        "GridGuard@2026",
        "not-a-valid-bcrypt-hash",
    ) is False


# --------------------------------------------------
# Redis JWT blacklist
# --------------------------------------------------

class FakeBlacklistRedis:
    def __init__(self):
        self.values = {}
        self.ttls = {}

    def setex(self, key, ttl, value):
        self.values[key] = value
        self.ttls[key] = ttl

    def exists(self, key):
        return int(key in self.values)


def test_blacklist_token_uses_remaining_ttl(monkeypatch):
    fake_redis = FakeBlacklistRedis()
    monkeypatch.setattr(token_blacklist, "redis_client", fake_redis)
    monkeypatch.setattr(token_blacklist.time, "time", lambda: 1000.0)

    token_blacklist.blacklist_token("sample.jwt.token", 1120)

    key = token_blacklist._get_blacklist_key("sample.jwt.token")
    assert fake_redis.values[key] == "revoked"
    assert fake_redis.ttls[key] == 120


def test_blacklisted_token_is_detected(monkeypatch):
    fake_redis = FakeBlacklistRedis()
    monkeypatch.setattr(token_blacklist, "redis_client", fake_redis)

    token = "sample.jwt.token"
    token_blacklist.blacklist_token(token, 9999999999)

    assert token_blacklist.is_token_blacklisted(token) is True
    assert token_blacklist.is_token_blacklisted("another.token") is False


def test_expired_token_is_not_added_to_blacklist(monkeypatch):
    fake_redis = FakeBlacklistRedis()
    monkeypatch.setattr(token_blacklist, "redis_client", fake_redis)
    monkeypatch.setattr(token_blacklist.time, "time", lambda: 2000.0)

    token_blacklist.blacklist_token("expired.jwt.token", 1999)

    assert fake_redis.values == {}


def test_empty_token_is_rejected():
    with pytest.raises(ValueError):
        token_blacklist.is_token_blacklisted("")


# --------------------------------------------------
# Login brute-force protection
# --------------------------------------------------

class FakeLoginRedis:
    def __init__(self, values=None):
        self.values = values or {}
        self.eval_calls = []
        self.deleted = []

    def mget(self, *keys):
        return [self.values.get(key) for key in keys]

    def eval(self, script, numkeys, *args):
        self.eval_calls.append((script, numkeys, args))
        return 1

    def delete(self, key):
        self.deleted.append(key)
        self.values.pop(key, None)


def test_login_not_blocked_below_attempt_limit(monkeypatch):
    fake_redis = FakeLoginRedis()
    monkeypatch.setattr(login_protection, "redis_client", fake_redis)

    assert login_protection.is_login_blocked(
        "user@example.com",
        "192.0.2.10",
    ) is False


def test_login_blocked_when_account_reaches_limit(monkeypatch):
    email = "user@example.com"
    ip = "192.0.2.10"

    email_key = login_protection._key("email", email)
    fake_redis = FakeLoginRedis({
        email_key: str(login_protection.MAX_FAILED_ATTEMPTS),
    })
    monkeypatch.setattr(login_protection, "redis_client", fake_redis)

    assert login_protection.is_login_blocked(email, ip) is True


def test_failed_login_increments_redis_counters(monkeypatch):
    fake_redis = FakeLoginRedis()
    monkeypatch.setattr(login_protection, "redis_client", fake_redis)

    login_protection.record_failed_login(
        "user@example.com",
        "192.0.2.10",
    )

    assert len(fake_redis.eval_calls) == 1
    _, numkeys, args = fake_redis.eval_calls[0]
    assert numkeys == 2
    assert int(args[2]) == login_protection.LOCKOUT_WINDOW_SECONDS


def test_successful_login_clears_account_failures(monkeypatch):
    fake_redis = FakeLoginRedis()
    monkeypatch.setattr(login_protection, "redis_client", fake_redis)

    login_protection.clear_account_login_failures("user@example.com")

    assert fake_redis.deleted == [
        login_protection._key("email", "user@example.com")
    ]
