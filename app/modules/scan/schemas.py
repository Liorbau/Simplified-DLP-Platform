"""Request and response bodies for /api/scan."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.common.fields import RequestModel, ScanText


class ScanRequest(RequestModel):
    text: ScanText
    dataset_id: UUID


class DetectedObject(BaseModel):
    id: UUID
    name: str
    match_count: int


class ScanResponse(BaseModel):
    status: Literal["match", "not matched"]
    detected_objects: list[DetectedObject] | None = None
