"""HTTP endpoints for /api/datatypes."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.db import SessionDep
from app.modules.datatypes import service
from app.modules.datatypes.models import DataType
from app.modules.datatypes.schemas import DataTypeRequest, DataTypeResponse

router = APIRouter(prefix="/api/datatypes", tags=["Data Types"])


@router.get("", response_model=list[DataTypeResponse])
def list_data_types(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[DataType]:
    return service.list_data_types(session, limit, offset)


@router.post("", response_model=DataTypeResponse, status_code=status.HTTP_201_CREATED)
def create_data_type(request: DataTypeRequest, session: SessionDep) -> DataType:
    return service.create_data_type(session, request)


@router.get("/{data_type_id}", response_model=DataTypeResponse)
def get_data_type(data_type_id: UUID, session: SessionDep) -> DataType:
    return service.get_data_type(session, data_type_id)


@router.put("/{data_type_id}", response_model=DataTypeResponse)
def replace_data_type(
    data_type_id: UUID, request: DataTypeRequest, session: SessionDep
) -> DataType:
    return service.replace_data_type(session, data_type_id, request)


@router.delete("/{data_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data_type(data_type_id: UUID, session: SessionDep) -> None:
    service.delete_data_type(session, data_type_id)
