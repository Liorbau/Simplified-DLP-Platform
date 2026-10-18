"""The scan endpoint end to end: threshold, OR logic, ordering and the spec's response shapes."""

import uuid

from fastapi.testclient import TestClient

from app.main import app

CLIENT = TestClient(app)


def _data_set_id(*data_types: tuple[str, list[str], int]) -> str:
    ids = [
        CLIENT.post(
            "/api/datatypes",
            json={"name": name, "type": "keywords", "content": content, "threshold": threshold},
        ).json()["id"]
        for name, content, threshold in data_types
    ]
    return CLIENT.post("/api/datasets", json={"name": "HR", "data_type_ids": ids}).json()["id"]


def _scan(data_set_id: str, text: str) -> dict:
    return CLIENT.post("/api/scan", json={"dataset_id": data_set_id, "text": text}).json()


def test_below_threshold_is_exactly_not_matched() -> None:
    data_set_id = _data_set_id(("Financial", ["salary", "bonus"], 2))
    assert _scan(data_set_id, "Payroll runs Friday, salary attached") == {"status": "not matched"}


def test_any_data_type_reaching_its_threshold_matches_strongest_first() -> None:
    data_set_id = _data_set_id(("Financial", ["salary", "bonus"], 2), ("Falcon", ["falcon"], 1))
    result = _scan(data_set_id, "The salary and bonus numbers for Falcon are attached.")
    assert result["status"] == "match"
    detections = [(item["name"], item["match_count"]) for item in result["detected_objects"]]
    assert detections == [("Financial", 2), ("Falcon", 1)]


def test_unknown_data_set_is_422_never_not_matched() -> None:
    response = CLIENT.post("/api/scan", json={"dataset_id": str(uuid.uuid4()), "text": "salary"})
    assert response.status_code == 422
    assert response.json()["code"] == "UNKNOWN_DATASET"
