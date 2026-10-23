import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Ensures database tables are initialized upon startup and handles graceful shutdown.
    """
    # Create all defined tables in PostgreSQL if they don't already exist
    Base.metadata.create_all(bind=engine)
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
    "*",                      # Permissive in dev to allow mobile emulator and IoT simulator connections
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount authentication route handlers
app.include_router(auth_router)


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
