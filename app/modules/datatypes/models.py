"""The data_types table."""

import uuid

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DataType(Base):
    __tablename__ = "data_types"
    __table_args__ = (
        CheckConstraint("threshold >= 1", name="threshold_at_least_one"),
        CheckConstraint("type IN ('keywords')", name="type_is_known"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(1000))
    type: Mapped[str] = mapped_column(String(20))
    content: Mapped[list[str]] = mapped_column(ARRAY(Text))
    threshold: Mapped[int]
    case_sensitive: Mapped[bool]
