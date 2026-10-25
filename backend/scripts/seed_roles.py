import os
import sys
from pathlib import Path

# Add project root directory to sys.path to enable clean imports when running standalone
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from backend.src.database import Base, SessionLocal, engine
from backend.src.models import Permission, Role

# Definition of granular permissions for GridGuard smart grid platform
SYSTEM_PERMISSIONS = [
    {"name": "users:manage", "description": "Create, update, and manage system user accounts"},
    {"name": "substations:read", "description": "View electrical substation details and telemetry"},
    {"name": "substations:write", "description": "Register and update electrical substations"},
    {"name": "grid:control", "description": "Execute critical breaker trip and switch operations"},
    {"name": "alerts:view", "description": "Monitor cybersecurity and electrical anomaly alerts"},
    {"name": "audit:read", "description": "Access security and system operation audit logs"},
]

# Definition of initial system roles and their assigned permission mappings
SYSTEM_ROLES = [
    {
        "name": "Admin",
        "description": "System administrator with comprehensive administrative access",
        "permissions": [
            "users:manage",
            "substations:read",
            "substations:write",
            "grid:control",
            "alerts:view",
            "audit:read",
        ],
    },
    {
        "name": "Engineer",
        "description": "Grid electrical engineer with operational and control access",
        "permissions": [
            "substations:read",
            "substations:write",
            "grid:control",
            "alerts:view",
        ],
    },
    {
        "name": "Technician",
        "description": "Field technician with read-only inspection and monitoring access",
        "permissions": [
            "substations:read",
            "alerts:view",
        ],
    },
]


def seed_roles() -> None:
    """
    Idempotently populate database with baseline system permissions and roles.
    Safe to execute repeatedly without duplicating records or encountering conflicts.
    """
    # Guarantee tables are created in the database first
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("--- Starting GridGuard Role & Permission Seeding ---")

        # 1. Seed Permissions idempotently
        permission_map = {}
        for perm_info in SYSTEM_PERMISSIONS:
            existing_perm = (
                db.query(Permission)
                .filter(Permission.name == perm_info["name"])
                .first()
            )
            if not existing_perm:
                existing_perm = Permission(
                    name=perm_info["name"],
                    description=perm_info["description"],
                )
                db.add(existing_perm)
                print(f" [+] Created permission: {perm_info['name']}")
            else:
                print(f" [=] Permission already exists: {perm_info['name']}")

            permission_map[perm_info["name"]] = existing_perm

        db.commit()

        # Refresh permission instances into session
        for perm in permission_map.values():
            db.refresh(perm)

        # 2. Seed Roles and link their assigned permissions idempotently
        for role_info in SYSTEM_ROLES:
            role = db.query(Role).filter(Role.name == role_info["name"]).first()
            if not role:
                role = Role(
                    name=role_info["name"],
                    description=role_info["description"],
                )
                db.add(role)
                print(f" [+] Created role: {role_info['name']}")
            else:
                print(f" [=] Role already exists: {role_info['name']}")

            # Associate designated permissions with the role
            assigned_perms = [
                permission_map[p_name]
                for p_name in role_info["permissions"]
                if p_name in permission_map
            ]
            role.permissions = assigned_perms

        db.commit()
        print("--- Seeding Completed Successfully ---")

    except Exception as error:
        db.rollback()
        print(f"[!] Seeding failed: {error}")
        raise error
    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()
