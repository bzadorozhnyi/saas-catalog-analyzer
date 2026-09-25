import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.enums.request_status_enum import RequestStatusEnum
from app.enums.request_type_enum import RequestTypeEnum
from app.models.base import BaseModel


class Request(BaseModel):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_type: Mapped[RequestTypeEnum] = mapped_column(
        SQLAlchemyEnum(RequestTypeEnum), nullable=False
    )
    status: Mapped[RequestStatusEnum] = mapped_column(
        SQLAlchemyEnum(RequestStatusEnum), nullable=False, default=RequestStatusEnum.PENDING
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
