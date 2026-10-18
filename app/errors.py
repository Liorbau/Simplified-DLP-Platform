"""The API's error catalog, and the handlers that render every error as RFC 9457 Problem Details."""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"

logger = logging.getLogger(__name__)


class AppError(Exception):
    code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str, **extra: object) -> None:
        super().__init__(detail)
        self.detail = detail
        self.extra = extra


class DataTypeNotFound(AppError):
    code = "DATA_TYPE_NOT_FOUND"


class DataSetNotFound(AppError):
    code = "DATASET_NOT_FOUND"


class DuplicateName(AppError):
    code = "DUPLICATE_NAME"


class DataTypeInUse(AppError):
    code = "DATA_TYPE_IN_USE"


class UnknownDataTypes(AppError):
    code = "UNKNOWN_DATA_TYPES"


class UnknownDataSet(AppError):
    code = "UNKNOWN_DATASET"


STATUS_BY_CODE: dict[str, HTTPStatus] = {
    AppError.code: HTTPStatus.INTERNAL_SERVER_ERROR,
    DataTypeNotFound.code: HTTPStatus.NOT_FOUND,
    DataSetNotFound.code: HTTPStatus.NOT_FOUND,
    DuplicateName.code: HTTPStatus.CONFLICT,
    DataTypeInUse.code: HTTPStatus.CONFLICT,
    UnknownDataTypes.code: HTTPStatus.UNPROCESSABLE_ENTITY,
    UnknownDataSet.code: HTTPStatus.UNPROCESSABLE_ENTITY,
}


def register_error_handlers(app: FastAPI) -> FastAPI:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
    return app


def _problem(
    status: HTTPStatus,
    code: str,
    detail: str,
    headers: dict[str, str] | None = None,
    **extra: object,
) -> JSONResponse:
    body = {
        "type": "about:blank",
        "title": status.phrase,
        "status": status.value,
        "detail": detail,
        "code": code,
        **extra,
    }
    return JSONResponse(
        jsonable_encoder(body), status_code=status, headers=headers, media_type=PROBLEM_JSON
    )


def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return _problem(STATUS_BY_CODE[exc.code], exc.code, exc.detail, **exc.extra)


def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    if any(error["type"] == "json_invalid" for error in exc.errors()):
        return _problem(HTTPStatus.BAD_REQUEST, "MALFORMED_JSON", "Request body is not valid JSON.")
    # Pydantic's raw errors include the submitted value; it is dropped so scan text is never echoed.
    errors = [
        {"field": ".".join(str(part) for part in error["loc"][1:]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return _problem(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        "Request validation failed.",
        errors=errors,
    )


def _handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    status = HTTPStatus(exc.status_code)
    return _problem(status, status.name, str(exc.detail), headers=exc.headers)


def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _problem(
        HTTPStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "An unexpected error occurred."
    )
