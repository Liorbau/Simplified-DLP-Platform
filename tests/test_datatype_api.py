"""Data Types endpoints over HTTP: status codes and response shapes."""

import uuid

from fastapi.testclient import TestClient

from app.main import app

CLIENT = TestClient(app)
FINANCIAL = {"name": "Financial", "type": "keywords", "content": ["salary"], "threshold": 2}


def test_create_returns_201_with_id_and_defaults() -> None:
    response = CLIENT.post("/api/datatypes", json=FINANCIAL)
    assert response.status_code == 201
    assert response.json() == {
        **FINANCIAL,
        "id": response.json()["id"],
        "description": "",
        "case_sensitive": False,
    }


def test_full_lifecycle_get_replace_list_delete() -> None:
    data_type_id = CLIENT.post("/api/datatypes", json=FINANCIAL).json()["id"]
    url = f"/api/datatypes/{data_type_id}"
    assert CLIENT.get(url).json()["name"] == "Financial"
    assert CLIENT.put(url, json={**FINANCIAL, "threshold": 3}).json()["threshold"] == 3
    assert [item["id"] for item in CLIENT.get("/api/datatypes").json()] == [data_type_id]
    assert CLIENT.delete(url).status_code == 204
    assert CLIENT.get(url).status_code == 404


def test_unknown_id_is_404_problem_details() -> None:
    response = CLIENT.get(f"/api/datatypes/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["code"] == "DATA_TYPE_NOT_FOUND"


def test_duplicate_name_is_409() -> None:
    CLIENT.post("/api/datatypes", json=FINANCIAL)
    assert CLIENT.post("/api/datatypes", json=FINANCIAL).status_code == 409


def test_limit_above_200_is_rejected() -> None:
    assert CLIENT.get("/api/datatypes?limit=201").status_code == 422


def test_threshold_beyond_any_possible_count_is_422() -> None:
    response = CLIENT.post("/api/datatypes", json={**FINANCIAL, "threshold": 10**20})
    assert response.status_code == 422
