import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, ForeignKey, Boolean, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Repository(Base):
    __tablename__ = "repositories"

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

    # GitHub repository identifiers
    github_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)  # owner/repo
    owner: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Repository metadata
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    size: Mapped[int] = mapped_column(Integer, default=0)  # KB

    # Latest commit info
    latest_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    latest_commit_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latest_commit_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Sync tracking
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
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
    user: Mapped["User"] = relationship("User", back_populates="repositories")

    # Composite index for unique repo per user
    __table_args__ = (
        Index("ix_user_github_repo", "user_id", "github_id", unique=True),
    )