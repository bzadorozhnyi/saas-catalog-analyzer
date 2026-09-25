from enum import StrEnum


class LlmCallPurposeEnum(StrEnum):
    CLASSIFICATION = "CLASSIFICATION"
    EMBEDDING = "EMBEDDING"
    EXPLAIN_DUPLICATE = "EXPLAIN_DUPLICATE"
