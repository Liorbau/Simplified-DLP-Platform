"""HTTP endpoint for /api/scan."""

from fastapi import APIRouter

from app.db import SessionDep
from app.modules.scan import service
from app.modules.scan.schemas import ScanRequest, ScanResponse

router = APIRouter(prefix="/api/scan", tags=["Scan"])


@router.post("", response_model=ScanResponse, response_model_exclude_none=True)
def scan(request: ScanRequest, session: SessionDep) -> ScanResponse:
    return service.scan(session, request)
