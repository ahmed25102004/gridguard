
import bcrypt


def verify_password_timing_safe(
    provided_password: str,
    stored_hash: str,
) -> bool:
    """
    Verify a password against a bcrypt hash.

    For nonexistent users, the caller should verify against
    a pre-generated dummy bcrypt hash to reduce timing differences.
    """
    if not isinstance(provided_password, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    try:
        return bcrypt.checkpw(
            provided_password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False
