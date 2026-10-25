from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..models import Role, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Pydantic v2 Validation Schemas ---

class RegisterRequest(BaseModel):
    """Schema for new user registration payload."""
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = Field(default=None, max_length=100)
    role_name: str = Field(default="Technician", description="Initial role assignment (e.g. Technician, Engineer)")


class LoginRequest(BaseModel):
    """Schema for user credentials during login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for returning JWT token pairs."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for requesting a refreshed access token."""
    refresh_token: str


class UserResponse(BaseModel):
    """
    Public user profile schema.
    Strictly omits passwords and password hashes to ensure credential confidentiality.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    role: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


# --- Authentication Route Handlers ---

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
    """
    Register a new user account with a hashed password and assigned system role.
    Returns the created user profile without sensitive credentials.
    """
    # Check if a user with this email already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Validate that the specified role exists in the database
    role = db.query(Role).filter(Role.name == payload.role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{payload.role_name}' does not exist",
        )

    # Instantiate new User with bcrypt-hashed password
    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role_id=role.id,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        role=role.name,
        permissions=[p.name for p in role.permissions],
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT tokens",
)
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate a user with email and password.
    Returns a pair of JWT access and refresh tokens upon successful verification.
    """
    # Retrieve user record by email
    user = db.query(User).filter(User.email == payload.email).first()

    # Validate existence and verify password hash
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Enforce active account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Claims payload included inside access token
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role.name if user.role else None,
    }

    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
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
    """
    Validate a refresh token and issue a newly minted access token along with a rotated refresh token.
    """
    # Decode and validate refresh token signature and expiration
    token_payload = decode_token(payload.refresh_token)

    email: Optional[str] = token_payload.get("sub")
    token_type: Optional[str] = token_payload.get("type")

    # Reject if the token is not strictly a refresh token
    if not email or token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected a refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure the user exists and is still active
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

    # Issue newly refreshed token pair with token rotation
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
    """
    Retrieve the profile, role, and granular permissions for the currently authenticated user.
    Requires a valid Bearer access token in the Authorization header.
    """
    permissions = (
        [p.name for p in current_user.role.permissions]
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
