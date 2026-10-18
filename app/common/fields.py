"""Every input rule the API enforces, shared by all request schemas."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StrictBool, StringConstraints

MAX_KEYWORDS = 500
MAX_DATA_TYPES_PER_SET = 20
MAX_SCAN_CHARS = 100_000


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _clean_keywords(keywords: list[str]) -> list[str]:
    stripped = [keyword.strip() for keyword in keywords]
    if "" in stripped:
        raise ValueError("keywords must not be blank")
    return _dedupe(stripped)


def _dedupe[T](items: list[T]) -> list[T]:
    return list(dict.fromkeys(items))


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]
DataTypeKind = Literal["keywords"]
Threshold = Annotated[int, Field(ge=1, le=MAX_SCAN_CHARS, strict=True)]
CaseSensitive = StrictBool
Keywords = Annotated[
    list[Annotated[str, StringConstraints(max_length=100)]],
    Field(min_length=1, max_length=MAX_KEYWORDS),
    AfterValidator(_clean_keywords),
]
DataTypeIds = Annotated[
    list[UUID], Field(min_length=1, max_length=MAX_DATA_TYPES_PER_SET), AfterValidator(_dedupe)
]
ScanText = Annotated[str, Field(max_length=MAX_SCAN_CHARS)]
