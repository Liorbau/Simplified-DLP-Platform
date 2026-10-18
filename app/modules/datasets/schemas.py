"""Request and response bodies for /api/datasets."""

from uuid import UUID

from pydantic import ConfigDict

from app.common.fields import DataTypeIds, Name, RequestModel


class DataSetRequest(RequestModel):
    name: Name
    data_type_ids: DataTypeIds


class DataSetResponse(DataSetRequest):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
