import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, ForeignKey, Integer, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"

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
    owner: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Commit information
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    commit_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    commit_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Tree data stored as JSON
    tree_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Tree metadata
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_directories: Mapped[int] = mapped_column(Integer, default=0)
    total_size: Mapped[int] = mapped_column(Integer, default=0)  # bytes

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="snapshots")

    # Composite indexes
    __table_args__ = (
        Index("ix_user_github_commit", "user_id", "github_id", "commit_sha"),
        Index("ix_user_repo_created", "user_id", "owner", "name", "created_at"),
    )