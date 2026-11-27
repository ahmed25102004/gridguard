import pytest
from datetime import timedelta
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
from backend.src.models import Asset, Feeder, Location, Permission, Role, Substation, User

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


# Precomputed bcrypt hash for fast test execution (bypasses slow multi-round hashing)
PRECOMPUTED_HASH = "$2b$12$xQPi/stgq1nvQ3pLJfp8eO6of7FAwkQvWHeyb3Qi2EZuu8WCRDaCC"


@pytest.fixture(autouse=True)
def mock_redis_for_tests(monkeypatch):
    """Ensure Redis operations run against an isolated in-memory fake during tests."""
    import fakeredis
    from backend.src.helpers import login_protection, token_blacklist

    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(login_protection, "redis_client", fake_redis)
    monkeypatch.setattr(token_blacklist, "redis_client", fake_redis)
    return fake_redis


@pytest.fixture(scope="function")
def db_session():
    """Builds clean isolated database tables and seeds baseline infrastructure per test."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed Admin and Operator Roles
    perm_read = Permission(name="assets:read", description="Read grid assets")
    perm_write = Permission(name="assets:write", description="Write grid assets")
    role_admin = Role(name="Admin", description="Global Administrator", permissions=[perm_read, perm_write])
    role_op = Role(name="Operator", description="Substation Operator", permissions=[perm_read, perm_write])
    db.add_all([perm_read, perm_write, role_admin, role_op])
    db.commit()

    # Seed Admin User using fast precomputed hash
    admin_user = User(
        email="admin@gridguard.io",
        hashed_password=PRECOMPUTED_HASH,
        full_name="Grid Admin",
        role_id=role_admin.id,
        is_active=True,
    )
    db.add(admin_user)
    db.commit()

    # Seed Baseline Substations
    sub_alpha = Substation(
        name="Cairo North Primary",
        code="SUB-CAI-01",
        location="30.0444, 31.2357",
        voltage_level_kv=220.0,
        status="OPERATIONAL",
        created_by_id=admin_user.id,
    )
    sub_beta = Substation(
        name="Alexandria Industrial",
        code="SUB-ALX-02",
        location="31.2001, 29.9187",
        voltage_level_kv=132.0,
        status="OPERATIONAL",
        created_by_id=admin_user.id,
    )
    db.add_all([sub_alpha, sub_beta])
    db.commit()

    # Seed Feeders
    fdr_1 = Feeder(
        name="Industrial Feeder 1",
        code="FDR-CAI-01",
        voltage_level_kv=33.0,
        substation_id=sub_alpha.id,
    )
    db.add(fdr_1)
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides FastAPI TestClient wired to the isolated test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_headers(db_session):
    """Provides valid Bearer Authorization header for global administrator."""
    admin = db_session.query(User).filter(User.email == "admin@gridguard.io").first()
    token = create_access_token(
        data={"sub": admin.email, "role": "Admin", "type": "access"},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. Asset CRUD & Validation Tests
# ==============================================================================

def test_create_asset_success(client, admin_headers, db_session):
    """Verifies successful asset creation with nested spatial coordinates."""
    sub = db_session.query(Substation).first()
    payload = {
        "asset_id": "AST-TRF-101",
        "name": "Main Step-Down Transformer 1",
        "asset_type": "Transformer",
        "manufacturer": "ABB",
        "model_number": "Resibloc 2500kVA",
        "capacity_kva": 2500.0,
        "voltage_rating_kv": 33.0,
        "status": "Active",
        "health_score": 98.5,
        "substation_id": sub.id,
        "location": {
            "name": "Transformer Bay 1",
            "latitude": 30.0450,
            "longitude": 31.2360,
            "elevation_m": 25.0,
        },
    }

    response = client.post("/assets", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["asset_id"] == "AST-TRF-101"
    assert data["manufacturer"] == "ABB"
    assert data["location"]["latitude"] == 30.0450
    assert data["location"]["longitude"] == 31.2360


def test_create_duplicate_asset_id_rejected(client, admin_headers, db_session):
    """Verifies that duplicate asset_id codes are rejected with 409 Conflict."""
    sub = db_session.query(Substation).first()
    payload = {
        "asset_id": "AST-SWT-001",
        "name": "Bus Tie Circuit Breaker",
        "asset_type": "Switch",
        "manufacturer": "Schneider Electric",
        "status": "Active",
        "substation_id": sub.id,
    }

    res1 = client.post("/assets", json=payload, headers=admin_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = client.post("/assets", json=payload, headers=admin_headers)
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in res2.json()["detail"]


def test_get_asset_by_id(client, admin_headers, db_session):
    """Verifies retrieval of asset details with populated relationships."""
    sub = db_session.query(Substation).first()
    payload = {
        "asset_id": "AST-CBL-001",
        "name": "33kV XLPE Underground Cable",
        "asset_type": "Cable",
        "manufacturer": "El Sewedy Electric",
        "status": "Active",
        "substation_id": sub.id,
    }
    create_res = client.post("/assets", json=payload, headers=admin_headers)
    asset_id = create_res.json()["id"]

    res = client.get(f"/assets/{asset_id}", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["name"] == "33kV XLPE Underground Cable"
    assert data["substation"]["code"] == sub.code


def test_update_asset(client, admin_headers, db_session):
    """Verifies updating operational status and health score."""
    sub = db_session.query(Substation).first()
    payload = {
        "asset_id": "AST-MTR-001",
        "name": "Smart Feeder Meter",
        "asset_type": "Meter",
        "manufacturer": "Siemens",
        "status": "Active",
        "health_score": 95.0,
        "substation_id": sub.id,
    }
    create_res = client.post("/assets", json=payload, headers=admin_headers)
    asset_id = create_res.json()["id"]

    update_payload = {
        "status": "Maintenance",
        "health_score": 62.0,
    }
    update_res = client.put(f"/assets/{asset_id}", json=update_payload, headers=admin_headers)
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["status"] == "Maintenance"
    assert update_res.json()["health_score"] == 62.0


def test_delete_asset(client, admin_headers, db_session):
    """Verifies asset deletion and subsequent 404 response."""
    sub = db_session.query(Substation).first()
    payload = {
        "asset_id": "AST-POL-001",
        "name": "Distribution Steel Pole 14",
        "asset_type": "Pole",
        "manufacturer": "Local Manufacturer",
        "status": "Active",
        "substation_id": sub.id,
    }
    create_res = client.post("/assets", json=payload, headers=admin_headers)
    asset_id = create_res.json()["id"]

    del_res = client.delete(f"/assets/{asset_id}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_200_OK

    get_res = client.get(f"/assets/{asset_id}", headers=admin_headers)
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


# ==============================================================================
# 2. Pagination, Search & Multi-Filter Tests
# ==============================================================================

def test_list_assets_pagination_and_filters(client, admin_headers, db_session):
    """Verifies pagination and status/type/search filtering across multiple assets."""
    sub = db_session.query(Substation).first()

    # Seed multiple assets
    test_items = [
        ("AST-T1", "Transformer 1", "Transformer", "Active", "ABB"),
        ("AST-T2", "Transformer 2", "Transformer", "Maintenance", "Siemens"),
        ("AST-S1", "Switch 1", "Switch", "Fault", "Schneider Electric"),
        ("AST-C1", "Cable 1", "Cable", "Active", "El Sewedy"),
        ("AST-M1", "Meter 1", "Meter", "Active", "Siemens"),
    ]
    for code, name, atype, astatus, mfr in test_items:
        client.post(
            "/assets",
            json={
                "asset_id": code,
                "name": name,
                "asset_type": atype,
                "status": astatus,
                "manufacturer": mfr,
                "substation_id": sub.id,
            },
            headers=admin_headers,
        )

    # Test limit and pagination
    res_page = client.get("/assets?page=1&limit=2", headers=admin_headers)
    assert res_page.status_code == status.HTTP_200_OK
    data = res_page.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    # Test status filter
    res_fault = client.get("/assets?status=Fault", headers=admin_headers)
    assert len(res_fault.json()["items"]) == 1
    assert res_fault.json()["items"][0]["asset_id"] == "AST-S1"

    # Test type filter
    res_trafo = client.get("/assets?asset_type=Transformer", headers=admin_headers)
    assert len(res_trafo.json()["items"]) == 2

    # Test debounced search filter
    res_search = client.get("/assets?search=Schneider", headers=admin_headers)
    assert len(res_search.json()["items"]) == 1
    assert res_search.json()["items"][0]["manufacturer"] == "Schneider Electric"


# ==============================================================================
# 3. PostGIS Spatial Radius Query Tests
# ==============================================================================

def test_spatial_radius_query(client, admin_headers, db_session):
    """
    Verifies that spatial filtering accurately returns assets within a given radius
    and excludes assets outside the designated radius.
    """
    sub = db_session.query(Substation).first()

    # Center location: Tahrir Square, Cairo (30.0444, 31.2357)
    # Asset A: 500 meters away (30.0480, 31.2357) -> within 2 km radius
    client.post(
        "/assets",
        json={
            "asset_id": "AST-NEAR-01",
            "name": "Nearby Transformer",
            "asset_type": "Transformer",
            "manufacturer": "ABB",
            "substation_id": sub.id,
            "location": {"latitude": 30.0480, "longitude": 31.2357},
        },
        headers=admin_headers,
    )

    # Asset B: Alexandria (~180 km away) (31.2001, 29.9187) -> outside 10 km radius
    client.post(
        "/assets",
        json={
            "asset_id": "AST-FAR-01",
            "name": "Distant Alexandria Switch",
            "asset_type": "Switch",
            "manufacturer": "Siemens",
            "substation_id": sub.id,
            "location": {"latitude": 31.2001, "longitude": 29.9187},
        },
        headers=admin_headers,
    )

    # Query with center Cairo and 5km radius
    res = client.get(
        "/assets/spatial/radius?lat=30.0444&lon=31.2357&radius_km=5.0",
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_200_OK
    spatial_results = res.json()

    # Nearby asset must be present, distant asset must be excluded
    returned_codes = [item["asset"]["asset_id"] for item in spatial_results]
    assert "AST-NEAR-01" in returned_codes
    assert "AST-FAR-01" not in returned_codes
    assert spatial_results[0]["distance_km"] < 2.0


# ==============================================================================
# 4. Multi-Tenant Substation Isolation Tests
# ==============================================================================

def test_tenant_substation_isolation(client, db_session):
    """
    Verifies that an operator scoped to Substation Alpha cannot create or modify
    assets assigned to Substation Beta.
    """
    subs = db_session.query(Substation).all()
    sub_alpha = subs[0]
    sub_beta = subs[1]

    # Create an operator user assigned specifically to sub_alpha
    role_op = db_session.query(Role).filter(Role.name == "Operator").first()
    operator_user = User(
        email="operator.alpha@gridguard.io",
        hashed_password=PRECOMPUTED_HASH,
        full_name="Alpha Tech",
        role_id=role_op.id,
        is_active=True,
    )
    # Simulate substation scoping on operator
    operator_user.substation_id = sub_alpha.id
    db_session.add(operator_user)
    db_session.commit()

    token = create_access_token(
        data={"sub": operator_user.email, "role": "Operator", "type": "access"},
        expires_delta=timedelta(minutes=30),
    )
    op_headers = {"Authorization": f"Bearer {token}"}

    # 1. Operator creates asset in assigned substation -> Success
    res_allowed = client.post(
        "/assets",
        json={
            "asset_id": "AST-OP-ALPHA-01",
            "name": "Alpha Feeder Monitor",
            "asset_type": "Meter",
            "manufacturer": "Schneider Electric",
            "substation_id": sub_alpha.id,
        },
        headers=op_headers,
    )
    assert res_allowed.status_code == status.HTTP_201_CREATED

    # 2. Operator attempts to create asset in another substation -> 403 Forbidden
    res_forbidden = client.post(
        "/assets",
        json={
            "asset_id": "AST-OP-BETA-01",
            "name": "Illegal Beta Feeder Monitor",
            "asset_type": "Meter",
            "manufacturer": "Schneider Electric",
            "substation_id": sub_beta.id,
        },
        headers=op_headers,
    )
    assert res_forbidden.status_code == status.HTTP_403_FORBIDDEN
    assert "Tenant violation" in res_forbidden.json()["detail"]
