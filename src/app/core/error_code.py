from enum import StrEnum


class ErrorCode(StrEnum):
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    INTERNAL = "internal_error"
