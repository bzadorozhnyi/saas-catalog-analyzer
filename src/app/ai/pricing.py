from typing import NamedTuple


class ModelPrice(NamedTuple):
    input_per_1m: float
    output_per_1m: float


# USD per 1M tokens. Not user-configurable settings — these are provider price
# list values, hardcoded and updated here when OpenAI's pricing changes.
MODEL_PRICING: dict[str, ModelPrice] = {
    "gpt-4o-mini": ModelPrice(input_per_1m=0.15, output_per_1m=0.60),
    "text-embedding-3-small": ModelPrice(input_per_1m=0.02, output_per_1m=0.0),
}


def calculate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    price = MODEL_PRICING.get(model)
    if price is None:
        return None
    return (input_tokens * price.input_per_1m + output_tokens * price.output_per_1m) / 1_000_000
