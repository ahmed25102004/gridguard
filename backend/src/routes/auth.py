from typing import List, Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers.auth import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)

from ..helpers.login_protection import (
    is_login_blocked,
    record_failed_login,
    clear_account_login_failures,
)
from ..helpers.password_policy import validate_password_strength
from ..helpers.token_blacklist import (
    blacklist_token,
    is_token_blacklisted,
)
from ..models import Role, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    """Schema for new user registration."""
    email: EmailStr
    password: str = Field(
        min_length=8,
        description="Password must meet the password strength policy",
    )
    full_name: Optional[str] = Field(default=None, max_length=100)
    role_name: str = Field(default="Technician")


class LoginRequest(BaseModel):
    """Schema for login credentials."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing access and refresh JWTs."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request to refresh a token pair."""
    refresh_token: str


class UserResponse(BaseModel):
    """Public user profile; never exposes password hashes."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    role: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


def _check_token_blacklist(token: str) -> bool:
    """Fail closed if the blacklist cannot be checked."""
    try:
        return is_token_blacklisted(token)
    except redis.exceptions.RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )


def _revoke_token(token: str, expires_at: int) -> None:
    """Revoke a token until its actual expiration time."""
    try:
        blacklist_token(token, expires_at)
    except redis.exceptions.RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Create a user with a validated, hashed password."""
    validate_password_strength(payload.password)

    existing_user = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    role = (
        db.query(Role)
        .filter(Role.name == payload.role_name)
        .first()
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested role does not exist",
        )

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role_id=role.id,
        is_active=True,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        role=role.name,
        permissions=[permission.name for permission in role.permissions],
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT tokens",
)
def login_user(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user with rate limiting."""
    client_ip = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    try:
        if is_login_blocked(payload.email, client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )
    except redis.exceptions.RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )

    user = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )


    # Use the same public error for unknown users and incorrect passwords.
    password_hash = (
        user.hashed_password
        if user is not None
        else DUMMY_PASSWORD_HASH
    )

    password_valid = verify_password(payload.password, password_hash)

    if user is None or not password_valid:
        try:
            record_failed_login(payload.email, client_ip)
        except redis.exceptions.RedisError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    try:
        clear_account_login_failures(payload.email)
    except redis.exceptions.RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )

    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role.name if user.role else None,
    }

    return TokenResponse(
        access_token=create_access_token(data=token_data),
        refresh_token=create_refresh_token(
            data={"sub": user.email, "user_id": user.id}
        ),
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token using a valid refresh token",
)
def refresh_access_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Validate, revoke, and rotate a refresh token."""
    token_payload = decode_token(payload.refresh_token)

    email = token_payload.get("sub")
    token_type = token_payload.get("type")
    expires_at = token_payload.get("exp")

    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: expected a refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if (
        not email
        or not isinstance(expires_at, (int, float))
        or isinstance(expires_at, bool)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if _check_token_blacklist(payload.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Revoke the old refresh token before returning a replacement.
    # If Redis is unavailable, fail closed and do not issue new tokens.
    _revoke_token(payload.refresh_token, int(expires_at))

    new_access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role.name if user.role else None,
        }
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve authenticated user profile",
)
def get_authenticated_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the authenticated user."""
    permissions = (
        [permission.name for permission in current_user.role.permissions]
        if current_user.role
        else []
    )

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        role=current_user.role.name if current_user.role else None,
        permissions=permissions,
    )