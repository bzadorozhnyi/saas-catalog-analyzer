from typing import NamedTuple


class SimilarPair(NamedTuple):
    name_a: str
    name_b: str
    similarity: float
