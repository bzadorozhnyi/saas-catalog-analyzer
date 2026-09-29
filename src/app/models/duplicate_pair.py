import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.enums.duplicate_verdict_enum import DuplicateVerdictEnum
from app.models.base import BaseModel


class DuplicatePair(BaseModel):
    __tablename__ = "duplicate_pairs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    check_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("duplicate_checks.id"), nullable=False
    )
    name_a: Mapped[str] = mapped_column(String(255), nullable=False)
    name_b: Mapped[str] = mapped_column(String(255), nullable=False)
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[DuplicateVerdictEnum] = mapped_column(
        SQLAlchemyEnum(DuplicateVerdictEnum), nullable=False
    )
    is_duplicate: Mapped[bool | None] = mapped_column(nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    overlapping_features: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    explained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
