.PHONY: lint format types test check

lint:
	uv run ruff check .

format:
	uv run ruff format .

types:
	uv run ty check .

test:
	uv run pytest

seed:
	uv run python scripts/seed_catalog.py

check: lint types test
