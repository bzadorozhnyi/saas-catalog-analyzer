import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import BaseModel


class DuplicateCheck(BaseModel):
    __tablename__ = "duplicate_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subscription_names: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    duplicate_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    review_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
