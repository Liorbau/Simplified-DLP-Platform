"""Data Sets endpoints over HTTP, including the cross-module rules (D-012, D-013)."""

import uuid

from fastapi.testclient import TestClient

from app.main import app

CLIENT = TestClient(app)


def _data_type_id(name: str) -> str:
    body = {"name": name, "type": "keywords", "content": ["salary"], "threshold": 1}
    return CLIENT.post("/api/datatypes", json=body).json()["id"]


def test_create_returns_201_with_linked_ids() -> None:
    data_type_id = _data_type_id("Financial")
    response = CLIENT.post("/api/datasets", json={"name": "HR", "data_type_ids": [data_type_id]})
    assert response.status_code == 201
    assert response.json()["data_type_ids"] == [data_type_id]


def test_unknown_data_type_id_is_422_and_listed() -> None:
    missing = str(uuid.uuid4())
    response = CLIENT.post("/api/datasets", json={"name": "HR", "data_type_ids": [missing]})
    assert response.status_code == 422
    assert response.json()["code"] == "UNKNOWN_DATA_TYPES"
    assert response.json()["data_type_ids"] == [missing]


def test_deleting_a_data_type_in_use_is_409_with_data_set_ids() -> None:
    data_type_id = _data_type_id("Financial")
    body = {"name": "HR", "data_type_ids": [data_type_id]}
    data_set_id = CLIENT.post("/api/datasets", json=body).json()["id"]
    response = CLIENT.delete(f"/api/datatypes/{data_type_id}")
    assert response.status_code == 409
    assert response.json()["dataset_ids"] == [data_set_id]


def test_full_lifecycle_get_replace_delete() -> None:
    first, second = _data_type_id("Financial"), _data_type_id("Medical")
    data_set_id = CLIENT.post(
        "/api/datasets", json={"name": "HR", "data_type_ids": [first]}
    ).json()["id"]
    url = f"/api/datasets/{data_set_id}"
    replaced = CLIENT.put(url, json={"name": "HR v2", "data_type_ids": [second]}).json()
    assert (replaced["name"], replaced["data_type_ids"]) == ("HR v2", [second])
    assert CLIENT.delete(url).status_code == 204
    assert CLIENT.get(url).json()["code"] == "DATASET_NOT_FOUND"


def test_renaming_to_a_taken_name_is_409() -> None:
    data_type_id = _data_type_id("Financial")
    CLIENT.post("/api/datasets", json={"name": "Taken", "data_type_ids": [data_type_id]})
    other = CLIENT.post("/api/datasets", json={"name": "Other", "data_type_ids": [data_type_id]})
    renamed = {"name": "Taken", "data_type_ids": [data_type_id]}
    response = CLIENT.put(f"/api/datasets/{other.json()['id']}", json=renamed)
    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_NAME"
