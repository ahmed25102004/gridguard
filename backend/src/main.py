from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes.assets import router as assets_router
from .routes.auth import router as auth_router
from .routes.work_orders import router as work_orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Ensures database tables are initialized upon startup, seeds baseline roles, and handles graceful shutdown.
    """
    try:
        # Create all defined tables in PostgreSQL/SQLite if they don't already exist
        Base.metadata.create_all(bind=engine)

        # Automatically seed baseline roles if not present
        from .models.role import Role
        from .database import SessionLocal
        with SessionLocal() as db:
            existing_roles = {r.name for r in db.query(Role).all()}
            for role_name in ["Admin", "Engineer", "Technician"]:
                if role_name not in existing_roles:
                    db.add(Role(name=role_name, description=f"Default {role_name} role"))
            db.commit()
            # Automatically seed sample substations if table is empty
            from .models.substation import Substation
            if db.query(Substation).count() == 0:
                s1 = Substation(id=1, name="Cairo North Primary", location="Cairo North, Zone 1", voltage_level_kv=220.0, status="OPERATIONAL")
                s2 = Substation(id=2, name="Alexandria West Terminal", location="Alexandria, Industrial Zone", voltage_level_kv=132.0, status="OPERATIONAL")
                db.add_all([s1, s2])
                db.commit()
    except Exception:
        # Fallback for offline testing or environments where engine is overridden
        pass
    yield


# Initialize the core FastAPI application
app = FastAPI(
    title="GridGuard Core API",
    description="Smart Grid Cybersecurity & Anomaly Monitoring Platform - Core Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) for web dashboard & mobile clients
origins = [
    "http://localhost:3000",  # React / Next.js local dashboard
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8080",
    "*",  # Permissive in dev to allow mobile emulator and IoT simulator connections
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount route handlers
app.include_router(auth_router)
app.include_router(assets_router)

# Mount work orders & dispatch route handlers
app.include_router(work_orders_router)


@app.get("/", tags=["System"])
def root():
    """Root endpoint displaying basic platform metadata."""
    return {
        "title": "GridGuard Core API",
        "status": "online",
        "docs_url": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
def health_check():
    """Health probe endpoint utilized by load balancers, Docker, and Kubernetes."""
    return {
        "status": "healthy",
        "service": "GridGuard Backend",
        "version": "1.0.0",
    }
