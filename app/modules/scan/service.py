"""Scan flow: load the Data Set and its Data Types, match each one, report detections."""

from sqlalchemy.orm import Session

from app.errors import UnknownDataSet
from app.modules.datasets import repository as datasets_repository
from app.modules.scan.matcher import count_matches
from app.modules.scan.schemas import DetectedObject, ScanRequest, ScanResponse


def scan(session: Session, request: ScanRequest) -> ScanResponse:
    data_set = datasets_repository.get(session, request.dataset_id)
    if data_set is None:
        raise UnknownDataSet(f"Data Set with id {request.dataset_id} doesn't exist")

    detected = []
    for data_type in data_set.data_types:
        match_count = count_matches(data_type.content, request.text, data_type.case_sensitive)
        if match_count >= data_type.threshold:
            detected.append(
                DetectedObject(id=data_type.id, name=data_type.name, match_count=match_count)
            )

    if not detected:
        return ScanResponse(status="not matched")
    detected.sort(key=lambda detection: (-detection.match_count, detection.name))
    return ScanResponse(status="match", detected_objects=detected)
