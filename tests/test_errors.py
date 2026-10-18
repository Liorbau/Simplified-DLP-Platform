"""Error catalog and RFC 9457 rendering, on an app with only the error handlers attached."""

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.errors import (
    PROBLEM_JSON,
    STATUS_BY_CODE,
    AppError,
    DataTypeInUse,
    register_error_handlers,
)

DATASET_ID = uuid.uuid4()


class _Body(BaseModel):
    threshold: int = Field(ge=1)


def _client() -> TestClient:
    app = register_error_handlers(FastAPI())

    @app.get("/in-use")
    def in_use() -> None:
        raise DataTypeInUse("Data Type is used by 1 Data Set.", dataset_ids=[DATASET_ID])

    @app.post("/body")
    def body(payload: _Body) -> _Body:
        return payload

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("error_class", [AppError, *AppError.__subclasses__()])
def test_every_error_code_has_a_status(error_class: type[AppError]) -> None:
    assert error_class.code in STATUS_BY_CODE


def test_app_error_renders_problem_details() -> None:
    response = _client().get("/in-use")
    assert response.status_code == 409
    assert response.headers["content-type"] == PROBLEM_JSON
    assert response.json() == {
        "type": "about:blank",
        "title": "Conflict",
        "status": 409,
        "detail": "Data Type is used by 1 Data Set.",
        "code": "DATA_TYPE_IN_USE",
        "dataset_ids": [str(DATASET_ID)],
    }


def test_validation_error_lists_fields_without_echoing_input() -> None:
    response = _client().post("/body", json={"threshold": 0})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"] == [
        {"field": "threshold", "message": "Input should be greater than or equal to 1"}
    ]


def test_validation_error_never_echoes_submitted_value() -> None:
    response = _client().post("/body", json={"threshold": "salary-of-the-ceo"})
    assert response.status_code == 422
    assert "salary-of-the-ceo" not in response.text


def test_malformed_json_is_a_bad_request() -> None:
    response = _client().post(
        "/body", content="{not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "MALFORMED_JSON"


def test_unknown_route_is_problem_details() -> None:
    response = _client().get("/nope")
    assert response.status_code == 404
    assert response.headers["content-type"] == PROBLEM_JSON
    assert response.json()["code"] == "NOT_FOUND"


def test_wrong_method_keeps_allow_header() -> None:
    response = _client().delete("/in-use")
    assert response.status_code == 405
    assert response.json()["code"] == "METHOD_NOT_ALLOWED"
    assert response.headers["allow"] == "GET"


def test_unexpected_error_is_generic_and_hides_internals() -> None:
    response = _client().get("/boom")
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert "secret" not in response.text
