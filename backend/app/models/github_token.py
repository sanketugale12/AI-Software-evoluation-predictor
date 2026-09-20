import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class GitHubToken(Base):
    __tablename__ = "github_tokens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Encrypted tokens (Fernet encrypted)
    encrypted_access_token: Mapped[str] = mapped_column(String(1000), nullable=False)
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )

    token_type: Mapped[str] = mapped_column(String(50), default="bearer")
    scope: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Token expiration (UTC)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="github_tokens")