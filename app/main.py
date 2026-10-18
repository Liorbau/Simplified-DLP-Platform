"""Application wiring: routers, exception handlers and the health check."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionDep
from app.errors import register_error_handlers
from app.modules.datasets.router import router as datasets_router
from app.modules.datatypes.router import router as datatypes_router
from app.modules.scan.router import router as scan_router

app = register_error_handlers(FastAPI(title="Simplified DLP Platform"))
app.include_router(datatypes_router)
app.include_router(datasets_router)
app.include_router(scan_router)


@app.get("/health")
def health(session: SessionDep) -> JSONResponse:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return JSONResponse(content={"status": "ok"})
