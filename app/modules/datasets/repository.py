"""Persistence for datasets and their links to data types."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import FOREIGN_KEY_VIOLATION, UNIQUE_VIOLATION
from app.db import save as save_row
from app.errors import DuplicateName, UnknownDataTypes
from app.modules.datasets.models import DataSet, dataset_data_types


def list_page(session: Session, limit: int, offset: int) -> Sequence[DataSet]:
    query = (
        select(DataSet)
        .options(selectinload(DataSet.data_types))
        .order_by(DataSet.name)
        .limit(limit)
        .offset(offset)
    )
    return session.scalars(query).all()


def get(session: Session, data_set_id: UUID) -> DataSet | None:
    return session.get(DataSet, data_set_id)


def save(session: Session, data_set: DataSet) -> DataSet:
    duplicate = DuplicateName(f"A Data Set named '{data_set.name}' already exists.")
    deleted_meanwhile = UnknownDataTypes("A linked Data Type was deleted while saving.")
    errors = {UNIQUE_VIOLATION: duplicate, FOREIGN_KEY_VIOLATION: deleted_meanwhile}
    return save_row(session, data_set, errors)


def delete(session: Session, data_set: DataSet) -> UUID:
    session.delete(data_set)
    session.commit()
    return data_set.id


def ids_using(session: Session, data_type_id: UUID) -> list[UUID]:
    query = select(dataset_data_types.c.dataset_id).where(
        dataset_data_types.c.data_type_id == data_type_id
    )
    return list(session.scalars(query))
