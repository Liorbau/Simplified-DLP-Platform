"""Business rules for Data Types."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import DataTypeInUse, DataTypeNotFound
from app.modules.datasets import repository as datasets_repository
from app.modules.datatypes import repository
from app.modules.datatypes.models import DataType
from app.modules.datatypes.schemas import DataTypeRequest


def list_data_types(session: Session, limit: int, offset: int) -> Sequence[DataType]:
    return repository.list_page(session, limit, offset)


def get_data_type(session: Session, data_type_id: UUID) -> DataType:
    data_type = repository.get(session, data_type_id)
    if data_type is None:
        raise DataTypeNotFound(f"Data Type with id {data_type_id} doesn't exist")
    return data_type


def create_data_type(session: Session, request: DataTypeRequest) -> DataType:
    return repository.save(session, DataType(**request.model_dump()))


def replace_data_type(session: Session, data_type_id: UUID, request: DataTypeRequest) -> DataType:
    data_type = get_data_type(session, data_type_id)
    for field, value in request.model_dump().items():
        setattr(data_type, field, value)
    return repository.save(session, data_type)


def delete_data_type(session: Session, data_type_id: UUID) -> UUID:
    data_type = get_data_type(session, data_type_id)
    dataset_ids = datasets_repository.ids_using(session, data_type_id)
    if dataset_ids:
        raise DataTypeInUse(
            f"Cannot delete Data Type {data_type_id}: used by {len(dataset_ids)} Data Sets",
            dataset_ids=dataset_ids,
        )
    return repository.delete(session, data_type)
