"""Data Types repository against the test database."""

import uuid

from sqlalchemy.orm import Session

from app.modules.datatypes import repository
from app.modules.datatypes.models import DataType


def _data_type(name: str) -> DataType:
    return DataType(
        name=name, description="", type="keywords", content=["x"], threshold=1, case_sensitive=False
    )


def test_get_returns_the_saved_data_type(session: Session) -> None:
    saved = repository.save(session, _data_type("Financial"))
    assert repository.get(session, saved.id) is saved


def test_get_returns_none_for_an_unknown_id(session: Session) -> None:
    assert repository.get(session, uuid.uuid4()) is None


def test_list_page_is_sorted_by_name_and_paginated(session: Session) -> None:
    for name in ["Medical", "Financial", "Legal"]:
        repository.save(session, _data_type(name))
    page = repository.list_page(session, limit=2, offset=1)
    assert [data_type.name for data_type in page] == ["Legal", "Medical"]


def test_delete_removes_the_row(session: Session) -> None:
    saved = repository.save(session, _data_type("Financial"))
    repository.delete(session, saved)
    assert repository.get(session, saved.id) is None
