"""The shared save helper: duplicates become the caller's conflict error, nothing half-saved."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import UNIQUE_VIOLATION, save
from app.errors import DuplicateName
from app.modules.datatypes.models import DataType


def _data_type(name: str) -> DataType:
    return DataType(
        name=name, description="", type="keywords", content=["x"], threshold=1, case_sensitive=False
    )


def test_duplicate_name_raises_the_given_conflict(session: Session) -> None:
    save(session, _data_type("Financial"), {UNIQUE_VIOLATION: DuplicateName("taken")})
    with pytest.raises(DuplicateName):
        save(session, _data_type("Financial"), {UNIQUE_VIOLATION: DuplicateName("taken")})
    assert session.scalar(select(func.count()).select_from(DataType)) == 1
