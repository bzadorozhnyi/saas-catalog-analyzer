from app.core.error_code import ErrorCode


class AppException(Exception):
    def __init__(self, msg: str, code: ErrorCode, details: list | None = None) -> None:
        self.msg = msg
        self.code = code
        self.details = details if details is not None else []
        super().__init__(msg)


class NotFoundException(AppException):
    def __init__(self, msg: str, details: list | None = None) -> None:
        super().__init__(msg=msg, code=ErrorCode.NOT_FOUND, details=details)


class InvalidException(AppException):
    def __init__(self, msg: str, details: list | None = None) -> None:
        super().__init__(msg=msg, code=ErrorCode.INVALID, details=details)
