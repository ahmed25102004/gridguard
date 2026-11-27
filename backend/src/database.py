import os
from collections.abc import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Load environment configurations
load_dotenv()


# Base declarative class for all SQLAlchemy 2.0 ORM models
class Base(DeclarativeBase):
    """Base class for all ORM models across the GridGuard platform."""

    pass


# Retrieve database connection URL from environment with a safe local fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gridguard_dev.db")

# Fix legacy PostgreSQL dialect scheme if provided by Supabase / Heroku
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure SQLAlchemy engine with connection pooler support for PostgreSQL / Supabase
engine_kwargs = {
    "pool_pre_ping": True,  # Test connection validity before execution
}

if "sqlite" not in DATABASE_URL:
    engine_kwargs.update(
        {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "300")),
        }
    )
else:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

if "sqlite" in DATABASE_URL:
    from sqlalchemy import event
    import geoalchemy2.admin.dialects.sqlite as sqlite_admin
    sqlite_admin.after_create = lambda *args, **kwargs: None
    sqlite_admin.before_drop = lambda *args, **kwargs: None

    @event.listens_for(engine, "connect")
    def _setup_sqlite_spatial(dbapi_connection, connection_record):
        dbapi_connection.create_function("GeomFromEWKT", 1, lambda x: x)
        dbapi_connection.create_function("AsEWKB", 1, lambda x: x)
        dbapi_connection.create_function("ST_AsBinary", 1, lambda x: x)

# Scoped session factory for database operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per HTTP request.
    Guarantees session release back to the connection pool upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
