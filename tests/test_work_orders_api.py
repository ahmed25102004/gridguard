import os
from datetime import datetime, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Disable SpatiaLite DDL triggers in SQLite for in-memory testing
import geoalchemy2.admin.dialects.sqlite as sqlite_admin
sqlite_admin.after_create = lambda *args, **kwargs: None
sqlite_admin.before_drop = lambda *args, **kwargs: None

from backend.src.database import Base, get_db
from backend.src.helpers.auth import create_access_token, hash_password
from backend.src.main import app
from backend.src.models import Permission, Role, Substation, User, WorkOrder
from backend.src.schemas.work_order import OutageCause, WorkOrderPriority, WorkOrderStatus

# Isolated in-memory SQLite database dedicated exclusively to the test suite
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

from sqlalchemy import event

@event.listens_for(test_engine, "connect")
def setup_sqlite_spatial_functions(dbapi_connection, connection_record):
    """Registers lightweight spatial stubs for in-memory SQLite test execution."""
    dbapi_connection.create_function("GeomFromEWKT", 1, lambda x: x)
    dbapi_connection.create_function("AsEWKB", 1, lambda x: x)
    dbapi_connection.create_function("ST_AsBinary", 1, lambda x: x)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(autouse=True)
def mock_redis_blacklist(monkeypatch):
    """Bypasses external Redis connection requirement in unit tests."""
    monkeypatch.setattr("backend.src.helpers.auth.is_token_blacklisted", lambda token: False)


@pytest.fixture(scope="function")
def db_session():
    """
    Builds clean in-memory tables, seeds baseline roles (Admin, Engineer, Technician)
    and baseline users for each test function.
    """
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # 1. Seed Roles
    perm = Permission(name="work_orders:all", description="Manage all work orders")
    role_admin = Role(name="Admin", description="Platform Administrator", permissions=[perm])
    role_engineer = Role(name="Engineer", description="Grid Operations Engineer", permissions=[perm])
    role_tech = Role(name="Technician", description="Field Technician", permissions=[perm])
    db.add_all([perm, role_admin, role_engineer, role_tech])
    db.commit()

    # 2. Seed Users
    admin_user = User(
        email="admin@gridguard.io",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin Director",
        role_id=role_admin.id,
        is_active=True,
    )
    engineer_user = User(
        email="engineer@gridguard.io",
        hashed_password=hash_password("EngineerPass123!"),
        full_name="Senior Grid Engineer",
        role_id=role_engineer.id,
        is_active=True,
    )
    tech_user = User(
        email="tech1@gridguard.io",
        hashed_password=hash_password("TechPass123!"),
        full_name="Lead Field Tech",
        role_id=role_tech.id,
        is_active=True,
    )
    tech_user_2 = User(
        email="tech2@gridguard.io",
        hashed_password=hash_password("TechPass123!"),
        full_name="Junior Field Tech",
        role_id=role_tech.id,
        is_active=True,
    )
    inactive_tech = User(
        email="inactive.tech@gridguard.io",
        hashed_password=hash_password("TechPass123!"),
        full_name="Inactive Technician",
        role_id=role_tech.id,
        is_active=False,
    )

    db.add_all([admin_user, engineer_user, tech_user, tech_user_2, inactive_tech])
    db.commit()

    # 3. Seed Substation for foreign key tests
    substation = Substation(
        id=1,
        name="Cairo North Primary",
        code="SUB-CAI-01",
        location="30.0444, 31.2357",
        voltage_level_kv=220.0,
        status="OPERATIONAL",
        created_by_id=admin_user.id,
    )
    db.add(substation)
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with get_db dependency overridden to use in-memory SQLite session.
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


# Authentication helper fixtures
@pytest.fixture
def admin_token() -> str:
    return create_access_token({"sub": "admin@gridguard.io", "role": "Admin"})


@pytest.fixture
def engineer_token() -> str:
    return create_access_token({"sub": "engineer@gridguard.io", "role": "Engineer"})


@pytest.fixture
def tech_token() -> str:
    return create_access_token({"sub": "tech1@gridguard.io", "role": "Technician"})


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def engineer_headers(engineer_token: str) -> dict:
    return {"Authorization": f"Bearer {engineer_token}"}


@pytest.fixture
def tech_headers(tech_token: str) -> dict:
    return {"Authorization": f"Bearer {tech_token}"}


# ============================================================================
# 1. Work Order Creation & RBAC Tests (POST /work-orders)
# ============================================================================

def test_create_work_order_as_engineer_success(client: TestClient, engineer_headers: dict):
    """Engineer successfully creates work order in initial 'Pending' state with metadata."""
    payload = {
        "title": "Substation Alpha Transformer Overheating",
        "description": "Oil temperature threshold exceeded 95C under peak load.",
        "substation_id": 1,
        "equipment_id": "AST-TRF-001",
        "priority": "High",
        "outage_cause": "Overload",
        "affected_customers_count": 1420,
    }
    response = client.post("/work-orders", json=payload, headers=engineer_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == payload["title"]
    assert data["status"] == WorkOrderStatus.PENDING.value
    assert data["priority"] == WorkOrderPriority.HIGH.value
    assert data["outage_cause"] == OutageCause.OVERLOAD.value
    assert data["affected_customers_count"] == 1420
    assert data["version_id"] == 1
    assert data["assigned_to_id"] is None
    assert data["completed_at"] is None
    assert data["verified_at"] is None


def test_create_work_order_as_admin_success(client: TestClient, admin_headers: dict):
    """Admin successfully creates work order with emergency priority."""
    payload = {
        "title": "Feeder Line 4 Tree Contact Tripping",
        "description": "Severe storm caused tree branch contact tripping breaker 4B.",
        "priority": "Emergency",
        "outage_cause": "Tree Contact",
        "affected_customers_count": 3500,
    }
    response = client.post("/work-orders", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "Pending"
    assert data["priority"] == "Emergency"
    assert data["outage_cause"] == "Tree Contact"


def test_create_work_order_as_technician_forbidden(client: TestClient, tech_headers: dict):
    """Technicians must be forbidden from creating work orders (HTTP 403)."""
    payload = {
        "title": "Unauthorized Tech Work Order",
        "description": "Technician cannot dispatch work orders.",
        "priority": "Medium",
    }
    response = client.post("/work-orders", json=payload, headers=tech_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_work_order_unauthenticated(client: TestClient):
    """Unauthenticated request must be rejected with HTTP 401."""
    response = client.post("/work-orders", json={"title": "No Auth"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_work_order_validation_errors(client: TestClient, engineer_headers: dict):
    """Pydantic validation: short title, negative customer count, invalid enum."""
    # 1. Title too short (< 3 chars)
    resp1 = client.post("/work-orders", json={"title": "AB"}, headers=engineer_headers)
    assert resp1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. Negative affected customers count
    resp2 = client.post(
        "/work-orders",
        json={"title": "Valid Title", "affected_customers_count": -5},
        headers=engineer_headers,
    )
    assert resp2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 3. Invalid outage cause enum
    resp3 = client.post(
        "/work-orders",
        json={"title": "Valid Title", "outage_cause": "Alien Attack"},
        headers=engineer_headers,
    )
    assert resp3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# 2. Work Order Retrieval & Query Filtering Tests (GET /work-orders)
# ============================================================================

def test_list_and_filter_work_orders(client: TestClient, engineer_headers: dict, tech_headers: dict):
    """Verify list retrieval and filtering by status, priority, and outage cause."""
    # Seed 3 distinct work orders
    client.post(
        "/work-orders",
        json={
            "title": "WO 1 - Storm Outage",
            "priority": "Emergency",
            "outage_cause": "Storm",
            "affected_customers_count": 500,
        },
        headers=engineer_headers,
    )
    client.post(
        "/work-orders",
        json={
            "title": "WO 2 - Routine Maintenance",
            "priority": "Low",
            "outage_cause": "Maintenance",
            "affected_customers_count": 0,
        },
        headers=engineer_headers,
    )
    client.post(
        "/work-orders",
        json={
            "title": "WO 3 - Equipment Failure",
            "priority": "High",
            "outage_cause": "Equipment Failure",
            "affected_customers_count": 120,
        },
        headers=engineer_headers,
    )

    # 1. All users (including Technician) can view list
    all_resp = client.get("/work-orders", headers=tech_headers)
    assert all_resp.status_code == status.HTTP_200_OK
    assert len(all_resp.json()) == 3

    # 2. Filter by priority
    filter_prio = client.get("/work-orders?priority=Emergency", headers=tech_headers)
    assert filter_prio.status_code == status.HTTP_200_OK
    prio_data = filter_prio.json()
    assert len(prio_data) == 1
    assert prio_data[0]["title"] == "WO 1 - Storm Outage"

    # 3. Filter by outage_cause
    filter_cause = client.get("/work-orders?outage_cause=Maintenance", headers=tech_headers)
    assert filter_cause.status_code == status.HTTP_200_OK
    cause_data = filter_cause.json()
    assert len(cause_data) == 1
    assert cause_data[0]["outage_cause"] == "Maintenance"


def test_get_work_order_by_id(client: TestClient, engineer_headers: dict, tech_headers: dict):
    """Retrieve single work order or return 404 for non-existent ID."""
    create_resp = client.post(
        "/work-orders",
        json={"title": "Specific Asset Inspection", "priority": "Medium"},
        headers=engineer_headers,
    )
    wo_id = create_resp.json()["id"]

    get_resp = client.get(f"/work-orders/{wo_id}", headers=tech_headers)
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["id"] == wo_id

    notFound = client.get("/work-orders/99999", headers=tech_headers)
    assert notFound.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# 3. Technician Assignment & Mobile Dispatch Engine (POST /work-orders/{id}/assign)
# ============================================================================

def test_assign_work_order_success_and_mobile_dispatch(
    client: TestClient,
    db_session,
    engineer_headers: dict,
):
    """
    Engineer assigns work order:
    - Status transitions from 'Pending' to 'Assigned'.
    - assigned_to_id is set to technician ID.
    - Mobile dispatch notification payload is delivered with technician details and timestamp.
    """
    create_resp = client.post(
        "/work-orders",
        json={"title": "Emergency Breaker Replacement", "priority": "Emergency"},
        headers=engineer_headers,
    )
    wo_id = create_resp.json()["id"]

    # Technician 1 ID lookup
    tech = db_session.query(User).filter(User.email == "tech1@gridguard.io").first()

    assign_payload = {"technician_id": tech.id}
    assign_resp = client.post(f"/work-orders/{wo_id}/assign", json=assign_payload, headers=engineer_headers)
    assert assign_resp.status_code == status.HTTP_200_OK

    data = assign_resp.json()
    assert "work_order" in data
    assert "dispatch_notification" in data

    # Check work order status update
    wo_data = data["work_order"]
    assert wo_data["id"] == wo_id
    assert wo_data["status"] == WorkOrderStatus.ASSIGNED.value
    assert wo_data["assigned_to_id"] == tech.id

    # Check dispatch notification trigger payload
    dispatch = data["dispatch_notification"]
    assert dispatch["work_order_id"] == wo_id
    assert dispatch["technician_id"] == tech.id
    assert dispatch["technician_email"] == "tech1@gridguard.io"
    assert dispatch["priority"] == "Emergency"
    assert dispatch["status"] == WorkOrderStatus.ASSIGNED.value
    assert "dispatched_at" in dispatch


def test_assign_work_order_as_technician_forbidden(
    client: TestClient,
    db_session,
    engineer_headers: dict,
    tech_headers: dict,
):
    """Field technicians cannot assign work orders (HTTP 403)."""
    create_resp = client.post(
        "/work-orders",
        json={"title": "Transformer Inspection"},
        headers=engineer_headers,
    )
    wo_id = create_resp.json()["id"]
    tech = db_session.query(User).filter(User.email == "tech1@gridguard.io").first()

    assign_resp = client.post(
        f"/work-orders/{wo_id}/assign",
        json={"technician_id": tech.id},
        headers=tech_headers,
    )
    assert assign_resp.status_code == status.HTTP_403_FORBIDDEN


def test_assign_work_order_to_nonexistent_or_inactive_technician(
    client: TestClient,
    db_session,
    engineer_headers: dict,
):
    """Assigning to non-existent technician returns 404; inactive returns 400."""
    create_resp = client.post(
        "/work-orders",
        json={"title": "Busbar Thermography"},
        headers=engineer_headers,
    )
    wo_id = create_resp.json()["id"]

    # 1. Non-existent technician ID
    resp_404 = client.post(
        f"/work-orders/{wo_id}/assign",
        json={"technician_id": 99999},
        headers=engineer_headers,
    )
    assert resp_404.status_code == status.HTTP_404_NOT_FOUND

    # 2. Inactive technician
    inactive_user = db_session.query(User).filter(User.email == "inactive.tech@gridguard.io").first()
    resp_400 = client.post(
        f"/work-orders/{wo_id}/assign",
        json={"technician_id": inactive_user.id},
        headers=engineer_headers,
    )
    assert resp_400.status_code == status.HTTP_400_BAD_REQUEST
    assert "inactive technician" in resp_400.json()["detail"]


# ============================================================================
# 4. Strict State Machine Lifecycle & Transitions (PUT /work-orders/{id}/status)
# ============================================================================

def test_full_valid_state_machine_lifecycle(
    client: TestClient,
    db_session,
    engineer_headers: dict,
    tech_headers: dict,
):
    """
    Valid Lifecycle Test:
    Pending -> Assigned -> In Progress -> Completed -> Verified
    Verifies timestamps and role permissions along the pipeline.
    """
    # 1. Create Work Order (Status: Pending)
    create_resp = client.post(
        "/work-orders",
        json={"title": "Complete Grid Diagnostic", "priority": "Medium"},
        headers=engineer_headers,
    )
    wo_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "Pending"

    # 2. Assign to Technician (Pending -> Assigned)
    tech = db_session.query(User).filter(User.email == "tech1@gridguard.io").first()
    assign_resp = client.post(
        f"/work-orders/{wo_id}/assign",
        json={"technician_id": tech.id},
        headers=engineer_headers,
    )
    assert assign_resp.status_code == status.HTTP_200_OK
    assert assign_resp.json()["work_order"]["status"] == "Assigned"

    # 3. Technician starts work (Assigned -> In Progress)
    progress_resp = client.put(
        f"/work-orders/{wo_id}/status",
        json={"status": "In Progress"},
        headers=tech_headers,
    )
    assert progress_resp.status_code == status.HTTP_200_OK
    assert progress_resp.json()["status"] == "In Progress"

    # 4. Technician finishes repair (In Progress -> Completed)
    completed_resp = client.put(
        f"/work-orders/{wo_id}/status",
        json={"status": "Completed", "resolution_notes": "Transformer oil replaced, tested OK."},
        headers=tech_headers,
    )
    assert completed_resp.status_code == status.HTTP_200_OK
    completed_data = completed_resp.json()
    assert completed_data["status"] == "Completed"
    assert completed_data["completed_at"] is not None

    # 5. Technician attempts to verify -> must be forbidden (HTTP 403)
    tech_verify_resp = client.put(
        f"/work-orders/{wo_id}/status",
        json={"status": "Verified"},
        headers=tech_headers,
    )
    assert tech_verify_resp.status_code == status.HTTP_403_FORBIDDEN

    # 6. Engineer verifies work order (Completed -> Verified)
    verify_resp = client.put(
        f"/work-orders/{wo_id}/status",
        json={"status": "Verified"},
        headers=engineer_headers,
    )
    assert verify_resp.status_code == status.HTTP_200_OK
    verify_data = verify_resp.json()
    assert verify_data["status"] == "Verified"
    assert verify_data["verified_at"] is not None


def test_transition_to_in_progress_without_technician_rejected(
    client: TestClient,
    engineer_headers: dict,
):
    """Work order cannot move to 'In Progress' if unassigned (HTTP 422)."""
    create_resp = client.post(
        "/work-orders",
        json={"title": "Unassigned Task"},
        headers=engineer_headers,
    )
    wo_id = create_resp.json()["id"]

    resp = client.put(
        f"/work-orders/{wo_id}/status",
        json={"status": "In Progress"},
        headers=engineer_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# 5. Blocking Invalid State Jumps (Strict HTTP 422 Enforcement)
# ============================================================================

def test_invalid_state_jump_pending_to_completed_rejected(
    client: TestClient,
    engineer_headers: dict,
):
    """Pending -> Completed is illegal and must return HTTP 422 with transition details."""
    create_resp = client.post(
        "/work-orders",
        json={"title": "Premature Completion Attempt"},
        headers=engineer_headers,
    )
    wo_id = create_resp.json()["id"]

    resp = client.put(
        f"/work-orders/{wo_id}/status",
        json={"status": "Completed"},
        headers=engineer_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = resp.json()["detail"]
    assert "Invalid status transition from 'Pending' to 'Completed'" in detail
    assert "Allowed transitions from 'Pending': ['Assigned']" in detail


def test_invalid_state_jump_completed_to_pending_rejected(
    client: TestClient,
    db_session,
    engineer_headers: dict,
    tech_headers: dict,
):
    """Completed -> Pending is strictly blocked (HTTP 422)."""
    # 1. Setup Completed Work Order
    create_resp = client.post("/work-orders", json={"title": "Jump Test"}, headers=engineer_headers)
    wo_id = create_resp.json()["id"]
    tech = db_session.query(User).filter(User.email == "tech1@gridguard.io").first()
    client.post(f"/work-orders/{wo_id}/assign", json={"technician_id": tech.id}, headers=engineer_headers)
    client.put(f"/work-orders/{wo_id}/status", json={"status": "In Progress"}, headers=tech_headers)
    client.put(f"/work-orders/{wo_id}/status", json={"status": "Completed"}, headers=tech_headers)

    # 2. Attempt illegal jump back to Pending
    jump_resp = client.put(
        f"/work-orders/{wo_id}/status",
        json={"status": "Pending"},
        headers=engineer_headers,
    )
    assert jump_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid status transition from 'Completed' to 'Pending'" in jump_resp.json()["detail"]


def test_invalid_state_jump_verified_to_in_progress_rejected(
    client: TestClient,
    db_session,
    engineer_headers: dict,
    tech_headers: dict,
):
    """Verified is a terminal state. Jumping from Verified -> In Progress returns HTTP 422."""
    create_resp = client.post("/work-orders", json={"title": "Terminal State Test"}, headers=engineer_headers)
    wo_id = create_resp.json()["id"]
    tech = db_session.query(User).filter(User.email == "tech1@gridguard.io").first()
    client.post(f"/work-orders/{wo_id}/assign", json={"technician_id": tech.id}, headers=engineer_headers)
    client.put(f"/work-orders/{wo_id}/status", json={"status": "In Progress"}, headers=tech_headers)
    client.put(f"/work-orders/{wo_id}/status", json={"status": "Completed"}, headers=tech_headers)
    client.put(f"/work-orders/{wo_id}/status", json={"status": "Verified"}, headers=engineer_headers)

    # Attempt to reopen from terminal Verified status
    reopen_resp = client.put(
        f"/work-orders/{wo_id}/status",
        json={"status": "In Progress"},
        headers=engineer_headers,
    )
    assert reopen_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid status transition from 'Verified' to 'In Progress'" in reopen_resp.json()["detail"]
    assert "Terminal State" in reopen_resp.json()["detail"]


def test_reassignment_blocked_in_completed_state(
    client: TestClient,
    db_session,
    engineer_headers: dict,
    tech_headers: dict,
):
    """Assigning a technician to a Completed work order must return HTTP 422."""
    create_resp = client.post("/work-orders", json={"title": "Reassignment Guard"}, headers=engineer_headers)
    wo_id = create_resp.json()["id"]
    tech1 = db_session.query(User).filter(User.email == "tech1@gridguard.io").first()
    tech2 = db_session.query(User).filter(User.email == "tech2@gridguard.io").first()

    client.post(f"/work-orders/{wo_id}/assign", json={"technician_id": tech1.id}, headers=engineer_headers)
    client.put(f"/work-orders/{wo_id}/status", json={"status": "In Progress"}, headers=tech_headers)
    client.put(f"/work-orders/{wo_id}/status", json={"status": "Completed"}, headers=tech_headers)

    assign_resp = client.post(
        f"/work-orders/{wo_id}/assign",
        json={"technician_id": tech2.id},
        headers=engineer_headers,
    )
    assert assign_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Cannot assign work order in 'Completed' status" in assign_resp.json()["detail"]
