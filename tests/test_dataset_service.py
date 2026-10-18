"""Data Sets service: links to existing Data Types only."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.errors import DataSetNotFound, UnknownDataTypes
from app.modules.datasets import service
from app.modules.datasets.schemas import DataSetRequest
from app.modules.datatypes import service as datatypes_service
from app.modules.datatypes.schemas import DataTypeRequest


def _data_type_id(session: Session, name: str) -> uuid.UUID:
    request = DataTypeRequest(name=name, type="keywords", content=["salary"], threshold=1)
    return datatypes_service.create_data_type(session, request).id


def test_create_links_the_requested_data_types(session: Session) -> None:
    ids = [_data_type_id(session, "Financial"), _data_type_id(session, "Medical")]
    data_set = service.create_data_set(session, DataSetRequest(name="HR", data_type_ids=ids))
    assert sorted(data_set.data_type_ids) == sorted(ids)


def test_unknown_ids_are_rejected_and_listed(session: Session) -> None:
    missing = uuid.uuid4()
    request = DataSetRequest(
        name="HR", data_type_ids=[_data_type_id(session, "Financial"), missing]
    )
    with pytest.raises(UnknownDataTypes) as raised:
        service.create_data_set(session, request)
    assert raised.value.extra == {"data_type_ids": [missing]}


def test_replace_swaps_the_linked_data_types(session: Session) -> None:
    financial, medical = _data_type_id(session, "Financial"), _data_type_id(session, "Medical")
    created = service.create_data_set(session, DataSetRequest(name="HR", data_type_ids=[financial]))
    request = DataSetRequest(name="HR v2", data_type_ids=[medical])
    replaced = service.replace_data_set(session, created.id, request)
    assert (replaced.name, replaced.data_type_ids) == ("HR v2", [medical])


def test_delete_then_get_is_not_found(session: Session) -> None:
    data_type_ids = [_data_type_id(session, "Financial")]
    created = service.create_data_set(
        session, DataSetRequest(name="HR", data_type_ids=data_type_ids)
    )
    service.delete_data_set(session, created.id)
    with pytest.raises(DataSetNotFound):
        service.get_data_set(session, created.id)
