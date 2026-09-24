import logfire
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.error_code import ErrorCode
from app.core.exceptions import AppException, InvalidException, NotFoundException


def resolve_status_code(exc: AppException) -> int:
    if isinstance(exc, NotFoundException):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, InvalidException):
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def log_unhandled_exception(request: Request, exc: Exception) -> None:
    logfire.exception(
        "Unhandled exception while processing {method} {path}",
        method=request.method,
        path=request.url.path,
        _exc_info=exc,
    )


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, AppException):
        return JSONResponse(
            status_code=resolve_status_code(exc),
            content={"code": exc.code, "msg": exc.msg, "details": exc.details},
        )

    log_unhandled_exception(request, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": ErrorCode.INTERNAL, "msg": "Internal server error", "details": []},
    )
