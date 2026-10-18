"""Input rules: keyword cleanup, id de-duplication, strict types and unknown fields."""

import uuid

import pytest
from pydantic import TypeAdapter, ValidationError

from app.common.fields import DataTypeIds, Keywords, RequestModel, ScanText, Threshold


class _Rule(RequestModel):
    threshold: Threshold


def test_keywords_are_trimmed_and_deduplicated() -> None:
    keywords = [" salary ", "salary", "bonus"]
    assert TypeAdapter(Keywords).validate_python(keywords) == ["salary", "bonus"]


def test_blank_keyword_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(Keywords).validate_python(["salary", "   "])


def test_data_type_ids_are_deduplicated() -> None:
    same_id = uuid.uuid4()
    assert TypeAdapter(DataTypeIds).validate_python([same_id, same_id]) == [same_id]


@pytest.mark.parametrize("payload", [{"threshold": "2"}, {"threshold": 2, "treshold": 2}])
def test_wrong_type_or_unknown_field_is_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _Rule.model_validate(payload)


def test_a_data_set_holds_at_most_20_data_types() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(DataTypeIds).validate_python([uuid.uuid4() for _ in range(21)])


def test_scan_text_is_at_most_100_000_characters() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(ScanText).validate_python("x" * 100_001)
