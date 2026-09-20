import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    github_id: Mapped[int] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    github_tokens: Mapped[list["GitHubToken"]] = relationship(
        "GitHubToken", back_populates="user", cascade="all, delete-orphan"
    )
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository", back_populates="user", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["RepositorySnapshot"]] = relationship(
        "RepositorySnapshot", back_populates="user", cascade="all, delete-orphan"
    )