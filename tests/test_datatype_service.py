"""Data Types service: not-found rule, create and replace."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.errors import DataTypeInUse, DataTypeNotFound, DuplicateName
from app.modules.datasets.models import DataSet
from app.modules.datatypes import service
from app.modules.datatypes.schemas import DataTypeRequest


def _request(name: str, threshold: int = 1) -> DataTypeRequest:
    return DataTypeRequest(name=name, type="keywords", content=["salary"], threshold=threshold)


def test_unknown_id_raises_not_found(session: Session) -> None:
    with pytest.raises(DataTypeNotFound):
        service.get_data_type(session, uuid.uuid4())


def test_replace_overwrites_every_field(session: Session) -> None:
    created = service.create_data_type(session, _request("Financial"))
    replaced = service.replace_data_type(session, created.id, _request("Finance", threshold=3))
    assert (replaced.id, replaced.name, replaced.threshold) == (created.id, "Finance", 3)


def test_replace_to_a_taken_name_raises_duplicate(session: Session) -> None:
    service.create_data_type(session, _request("Financial"))
    medical = service.create_data_type(session, _request("Medical"))
    with pytest.raises(DuplicateName):
        service.replace_data_type(session, medical.id, _request("Financial"))


def test_delete_removes_an_unused_data_type(session: Session) -> None:
    created = service.create_data_type(session, _request("Financial"))
    service.delete_data_type(session, created.id)
    with pytest.raises(DataTypeNotFound):
        service.get_data_type(session, created.id)


def test_delete_in_use_raises_with_the_data_set_ids(session: Session) -> None:
    created = service.create_data_type(session, _request("Financial"))
    data_set = DataSet(name="HR policy", data_types=[created])
    session.add(data_set)
    session.commit()
    with pytest.raises(DataTypeInUse) as raised:
        service.delete_data_type(session, created.id)
    assert raised.value.extra == {"dataset_ids": [data_set.id]}
