"""Persistence for data_types: queries in, model objects out."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import FOREIGN_KEY_VIOLATION, UNIQUE_VIOLATION, commit
from app.db import save as save_row
from app.errors import DataTypeInUse, DuplicateName
from app.modules.datatypes.models import DataType


def list_page(session: Session, limit: int, offset: int) -> Sequence[DataType]:
    query = select(DataType).order_by(DataType.name).limit(limit).offset(offset)
    return session.scalars(query).all()


def get(session: Session, data_type_id: UUID) -> DataType | None:
    return session.get(DataType, data_type_id)


def get_many(session: Session, data_type_ids: list[UUID]) -> Sequence[DataType]:
    return session.scalars(select(DataType).where(DataType.id.in_(data_type_ids))).all()


def save(session: Session, data_type: DataType) -> DataType:
    duplicate = DuplicateName(f"A Data Type named '{data_type.name}' already exists.")
    return save_row(session, data_type, {UNIQUE_VIOLATION: duplicate})


def delete(session: Session, data_type: DataType) -> UUID:
    data_type_id = data_type.id
    in_use = DataTypeInUse(f"Data Type {data_type_id} was linked to a Data Set while deleting.")
    session.delete(data_type)
    commit(session, {FOREIGN_KEY_VIOLATION: in_use})
    return data_type_id
