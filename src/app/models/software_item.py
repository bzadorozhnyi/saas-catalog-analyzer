from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.enums.software_category_enum import SoftwareCategoryEnum
from app.models.base import BaseModel
from app.models.constants import EMBEDDING_DIMENSIONS


class SoftwareItem(BaseModel):
    __tablename__ = "software_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[SoftwareCategoryEnum] = mapped_column(
        SQLAlchemyEnum(SoftwareCategoryEnum), nullable=False
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
