import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.enums.attempt_status_enum import AttemptStatusEnum
from app.models.base import BaseModel


class RequestAttempt(BaseModel):
    __tablename__ = "request_attempts"
    __table_args__ = (
        CheckConstraint(
            "status != 'FAILED' OR error_message IS NOT NULL",
            name="ck_request_attempts_failed_has_error_message",
        ),
        CheckConstraint(
            "status != 'SUCCEEDED' OR success_message IS NOT NULL",
            name="ck_request_attempts_succeeded_has_success_message",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AttemptStatusEnum] = mapped_column(
        SQLAlchemyEnum(AttemptStatusEnum), nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    success_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
