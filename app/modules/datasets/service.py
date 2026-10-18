"""Business rules for Data Sets."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import DataSetNotFound, UnknownDataTypes
from app.modules.datasets import repository
from app.modules.datasets.models import DataSet
from app.modules.datasets.schemas import DataSetRequest
from app.modules.datatypes import repository as datatypes_repository
from app.modules.datatypes.models import DataType


def list_data_sets(session: Session, limit: int, offset: int) -> Sequence[DataSet]:
    return repository.list_page(session, limit, offset)


def get_data_set(session: Session, data_set_id: UUID) -> DataSet:
    data_set = repository.get(session, data_set_id)
    if data_set is None:
        raise DataSetNotFound(f"Data Set with id {data_set_id} doesn't exist")
    return data_set


def create_data_set(session: Session, request: DataSetRequest) -> DataSet:
    data_types = _load_data_types(session, request.data_type_ids)
    return repository.save(session, DataSet(name=request.name, data_types=data_types))


def replace_data_set(session: Session, data_set_id: UUID, request: DataSetRequest) -> DataSet:
    data_set = get_data_set(session, data_set_id)
    data_set.data_types = _load_data_types(session, request.data_type_ids)
    # Rename last: earlier queries would autoflush a duplicate name outside save()'s 409 handling.
    data_set.name = request.name
    return repository.save(session, data_set)


def delete_data_set(session: Session, data_set_id: UUID) -> UUID:
    return repository.delete(session, get_data_set(session, data_set_id))


def _load_data_types(session: Session, data_type_ids: list[UUID]) -> list[DataType]:
    data_types = datatypes_repository.get_many(session, data_type_ids)
    found_ids = {data_type.id for data_type in data_types}
    unknown_ids = list(set(data_type_ids) - found_ids)
    if unknown_ids:
        raise UnknownDataTypes(
            f"{len(unknown_ids)} Data Type ids don't exist", data_type_ids=unknown_ids
        )
    return list(data_types)
