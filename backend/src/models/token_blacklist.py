from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime

from backend.src.database import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)

    token_hash = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    blacklisted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

