"""Races the service checks can't see: the database's foreign key decides, as a clean 4xx."""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import engine
from app.errors import DataTypeInUse, UnknownDataTypes
from app.modules.datasets import repository as datasets_repository
from app.modules.datasets.models import DataSet
from app.modules.datatypes import repository as datatypes_repository
from app.modules.datatypes.models import DataType


def _saved_data_type(session: Session) -> DataType:
    data_type = DataType(
        name="Financial",
        description="",
        type="keywords",
        content=["x"],
        threshold=1,
        case_sensitive=False,
    )
    return datatypes_repository.save(session, data_type)


def test_delete_racing_a_new_link_is_in_use(session: Session) -> None:
    data_type = _saved_data_type(session)
    datasets_repository.save(session, DataSet(name="HR", data_types=[data_type]))
    with pytest.raises(DataTypeInUse):
        datatypes_repository.delete(session, data_type)


def test_link_racing_a_delete_is_unknown_data_type(session: Session) -> None:
    data_type = _saved_data_type(session)
    with engine.begin() as other_request:
        other_request.execute(text("DELETE FROM data_types WHERE id = :id"), {"id": data_type.id})
    with pytest.raises(UnknownDataTypes):
        datasets_repository.save(session, DataSet(name="HR", data_types=[data_type]))
