"""Data Type request defaults and response mapping from a database row."""

import uuid

import pytest
from pydantic import ValidationError

from app.modules.datatypes.models import DataType
from app.modules.datatypes.schemas import DataTypeRequest, DataTypeResponse

MINIMAL_REQUEST = {"name": "Financial", "type": "keywords", "content": ["salary"], "threshold": 1}


def test_optional_fields_get_their_defaults() -> None:
    request = DataTypeRequest.model_validate(MINIMAL_REQUEST)
    assert request.description == ""
    assert request.case_sensitive is False


def test_type_is_required() -> None:
    without_type = {key: value for key, value in MINIMAL_REQUEST.items() if key != "type"}
    with pytest.raises(ValidationError):
        DataTypeRequest.model_validate(without_type)


def test_response_reads_a_database_row() -> None:
    row = DataType(id=uuid.uuid4(), description="", case_sensitive=False, **MINIMAL_REQUEST)
    response = DataTypeResponse.model_validate(row)
    assert response.id == row.id
    assert response.content == ["salary"]
