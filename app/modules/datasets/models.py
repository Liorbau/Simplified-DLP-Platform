"""The datasets table and its links to data types."""

import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.modules.datatypes.models import DataType

dataset_data_types = Table(
    "dataset_data_types",
    Base.metadata,
    Column("dataset_id", ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "data_type_id",
        ForeignKey("data_types.id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    ),
)


class DataSet(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    data_types: Mapped[list[DataType]] = relationship(secondary=dataset_data_types)

    @property
    def data_type_ids(self) -> list[uuid.UUID]:
        return [data_type.id for data_type in self.data_types]
