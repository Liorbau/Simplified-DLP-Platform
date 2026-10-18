"""Request and response bodies for /api/datatypes."""

from uuid import UUID

from pydantic import ConfigDict

from app.common.fields import (
    CaseSensitive,
    DataTypeKind,
    Description,
    Keywords,
    Name,
    RequestModel,
    Threshold,
)


class DataTypeRequest(RequestModel):
    name: Name
    description: Description = ""
    type: DataTypeKind
    content: Keywords
    threshold: Threshold
    case_sensitive: CaseSensitive = False


class DataTypeResponse(DataTypeRequest):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
