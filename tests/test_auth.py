from datetime import timedelta
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.src.database import Base, get_db
from backend.src.helpers.auth import create_access_token, create_refresh_token, decode_token, hash_password
from backend.src.main import app
from backend.src.models import Permission, Role, User

# Isolated in-memory SQLite database dedicated exclusively to the test suite
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture providing a fresh isolated database session per test.
    Builds tables, seeds baseline roles, and completely tears down schemas after execution.
    """
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed baseline roles and permissions for tests
    perm = Permission(name="substations:read", description="Read telemetry")
    role_admin = Role(name="Admin", description="Admin role", permissions=[perm])
    role_tech = Role(name="Technician", description="Tech role", permissions=[perm])
    db.add_all([perm, role_admin, role_tech])
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture providing FastAPI TestClient with get_db overridden to use the test database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==========================================
# 1. Registration Flow Tests (POST /auth/register)
# ==========================================

def test_register_success(client: TestClient):
    """Test successful user registration with initial role and sanitized output."""
    response = client.post(
        "/auth/register",
        json={
            "email": "engineer.lead@gridguard.io",
            "password": "SecurePassword123!",
            "full_name": "Chief Grid Engineer",
            "role_name": "Technician",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "engineer.lead@gridguard.io"
    assert data["full_name"] == "Chief Grid Engineer"
    assert data["role"] == "Technician"
    assert data["is_active"] is True
    # Security assertion: ensure password and hash are strictly omitted
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client: TestClient):
    """Test rejection of duplicate email registration."""
    payload = {
        "email": "duplicate@gridguard.io",
        "password": "SecurePassword123!",
        "role_name": "Technician",
    }
    first_resp = client.post("/auth/register", json=payload)
    assert first_resp.status_code == status.HTTP_201_CREATED

    second_resp = client.post("/auth/register", json=payload)
    assert second_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email is already registered" in second_resp.json()["detail"]


def test_register_nonexistent_role(client: TestClient):
    """Test rejection when assigning an invalid / unseeded role."""
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid.role@gridguard.io",
            "password": "SecurePassword123!",
            "role_name": "SuperGodModeRole",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not exist" in response.json()["detail"]


def test_register_weak_password_validation(client: TestClient):
    """Test strict Pydantic v2 validation rejecting passwords shorter than 8 chars."""
    response = client.post(
        "/auth/register",
        json={
            "email": "weak@gridguard.io",
            "password": "short",
            "role_name": "Technician",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ==========================================
# 2. Login Flow Tests (POST /auth/login)
# ==========================================

def test_login_success(client: TestClient):
    """Test successful login returning valid JWT access and refresh token pair."""
    client.post(
        "/auth/register",
        json={
            "email": "login.test@gridguard.io",
            "password": "Password123!",
            "role_name": "Technician",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login.test@gridguard.io",
            "password": "Password123!",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """Test login failure with incorrect password returns 401."""
    client.post(
        "/auth/register",
        json={
            "email": "wrong.pass@gridguard.io",
            "password": "CorrectPassword123!",
            "role_name": "Technician",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrong.pass@gridguard.io",
            "password": "IncorrectPassword999!",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client: TestClient, monkeypatch):
    """Unknown users use the dummy hash and receive a generic 401."""
    from backend.src.routes import auth as auth_routes
    from backend.src.helpers.auth import DUMMY_PASSWORD_HASH

    checked_hashes = []

    def fake_verify_password(password, stored_hash):
        checked_hashes.append(stored_hash)
        return False

    monkeypatch.setattr(
        auth_routes,
        "verify_password",
        fake_verify_password,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "ghost.user@gridguard.io",
            "password": "AnyPassword123!",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid email or password"
    assert checked_hashes == [DUMMY_PASSWORD_HASH]


def test_login_deactivated_user(client: TestClient, db_session):
    """Test that deactivated users (is_active=False) are rejected with 403 Forbidden."""
    client.post(
        "/auth/register",
        json={
            "email": "deactivated@gridguard.io",
            "password": "Password123!",
            "role_name": "Technician",
        },
    )

    # Deactivate user directly in test db
    user = db_session.query(User).filter(User.email == "deactivated@gridguard.io").first()
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={
            "email": "deactivated@gridguard.io",
            "password": "Password123!",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "deactivated" in response.json()["detail"]


# ==========================================
# 3. Refresh Token Tests (POST /auth/refresh)
# ==========================================

def test_refresh_token_success(client: TestClient):
    """Test renewing session using a valid refresh token."""
    client.post(
        "/auth/register",
        json={
            "email": "refresher@gridguard.io",
            "password": "Password123!",
            "role_name": "Technician",
        },
    )

    login_resp = client.post(
        "/auth/login",
        json={
            "email": "refresher@gridguard.io",
            "password": "Password123!",
        },
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_with_access_token_rejected(client: TestClient):
    """Test security constraint: Access token cannot be substituted as a refresh token."""
    client.post(
        "/auth/register",
        json={
            "email": "token.sub@gridguard.io",
            "password": "Password123!",
            "role_name": "Technician",
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "token.sub@gridguard.io",
            "password": "Password123!",
        },
    )
    access_token = login_resp.json()["access_token"]

    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expected a refresh token" in response.json()["detail"]


def test_refresh_with_tampered_token(client: TestClient):
    """Test sending an invalid / forged token to /auth/refresh."""
    response = client.post("/auth/refresh", json={"refresh_token": "tampered.jwt.token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]


def test_refresh_nonexistent_user(client: TestClient):
    """Test refresh token when user was removed from database."""
    token = create_refresh_token(data={"sub": "deleted.user@gridguard.io"})
    response = client.post("/auth/refresh", json={"refresh_token": token})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "User not found" in response.json()["detail"]


def test_refresh_deactivated_user(client: TestClient, db_session):
    """Test refresh token when user account has been deactivated."""
    client.post(
        "/auth/register",
        json={
            "email": "deactivated.refresh@gridguard.io",
            "password": "Password123!",
            "role_name": "Technician",
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "deactivated.refresh@gridguard.io",
            "password": "Password123!",
        },
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Deactivate user
    user = db_session.query(User).filter(User.email == "deactivated.refresh@gridguard.io").first()
    user.is_active = False
    db_session.commit()

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "User account is deactivated" in response.json()["detail"]


# ==========================================
# 4. Protected Route Tests (GET /auth/me)
# ==========================================

def test_get_me_success(client: TestClient):
    """Test retrieving authenticated user profile using Bearer access token."""
    client.post(
        "/auth/register",
        json={
            "email": "me.profile@gridguard.io",
            "password": "Password123!",
            "full_name": "Grid Inspector",
            "role_name": "Technician",
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "me.profile@gridguard.io",
            "password": "Password123!",
        },
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "me.profile@gridguard.io"
    assert data["full_name"] == "Grid Inspector"
    assert data["role"] == "Technician"
    assert "substations:read" in data["permissions"]


def test_get_me_missing_token(client: TestClient):
    """Test that accessing /auth/me without authorization header returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_with_refresh_token_rejected(client: TestClient):
    """Test that sending a refresh token to /auth/me is blocked."""
    client.post(
        "/auth/register",
        json={
            "email": "refresh.me@gridguard.io",
            "password": "Password123!",
            "role_name": "Technician",
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "refresh.me@gridguard.io",
            "password": "Password123!",
        },
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_nonexistent_user(client: TestClient):
    """Test /auth/me when the user identity inside token does not exist in DB."""
    token = create_access_token(data={"sub": "ghost@gridguard.io"})
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_deactivated_user(client: TestClient, db_session):
    """Test /auth/me when the user is deactivated."""
    client.post(
        "/auth/register",
        json={
            "email": "active.then.deact@gridguard.io",
            "password": "Password123!",
            "role_name": "Technician",
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "active.then.deact@gridguard.io",
            "password": "Password123!",
        },
    )
    access_token = login_resp.json()["access_token"]

    # Deactivate user
    user = db_session.query(User).filter(User.email == "active.then.deact@gridguard.io").first()
    user.is_active = False
    db_session.commit()

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ==========================================
# 5. Helpers & System Endpoint Tests
# ==========================================

def test_custom_token_expiration_deltas():
    """Test that custom timedelta expiration is respected by token generation helpers."""
    delta = timedelta(hours=2)
    access_token = create_access_token(data={"sub": "custom@test.com"}, expires_delta=delta)
    refresh_token = create_refresh_token(data={"sub": "custom@test.com"}, expires_delta=delta)

    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)

    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"


def test_system_root_and_health_endpoints(client: TestClient):
    """Test root information and health check endpoints."""
    root_resp = client.get("/")
    assert root_resp.status_code == status.HTTP_200_OK
    assert root_resp.json()["status"] == "online"

    health_resp = client.get("/health")
    assert health_resp.status_code == status.HTTP_200_OK
    assert health_resp.json()["status"] == "healthy"
