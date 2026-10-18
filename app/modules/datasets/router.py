"""HTTP endpoints for /api/datasets."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.db import SessionDep
from app.modules.datasets import service
from app.modules.datasets.models import DataSet
from app.modules.datasets.schemas import DataSetRequest, DataSetResponse

router = APIRouter(prefix="/api/datasets", tags=["Data Sets"])


@router.get("", response_model=list[DataSetResponse])
def list_data_sets(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[DataSet]:
    return service.list_data_sets(session, limit, offset)


@router.post("", response_model=DataSetResponse, status_code=status.HTTP_201_CREATED)
def create_data_set(request: DataSetRequest, session: SessionDep) -> DataSet:
    return service.create_data_set(session, request)


@router.get("/{data_set_id}", response_model=DataSetResponse)
def get_data_set(data_set_id: UUID, session: SessionDep) -> DataSet:
    return service.get_data_set(session, data_set_id)


@router.put("/{data_set_id}", response_model=DataSetResponse)
def replace_data_set(data_set_id: UUID, request: DataSetRequest, session: SessionDep) -> DataSet:
    return service.replace_data_set(session, data_set_id, request)


@router.delete("/{data_set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data_set(data_set_id: UUID, session: SessionDep) -> None:
    service.delete_data_set(session, data_set_id)
