import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    repository_url: Mapped[str] = mapped_column(String(500))
    repository_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("repositories.id"),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="queued",
    )

    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    # Versioning
    version: Mapped[int] = mapped_column(default=1)

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(default=0)

    # Cancellation
    cancelled: Mapped[bool] = mapped_column(default=False)

    # Progress tracking
    progress: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    # Commit SHA for pinned analysis (Phase 6)
    commit_sha: Mapped[Optional[str]] = mapped_column(
        String(40),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
