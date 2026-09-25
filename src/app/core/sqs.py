from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3

from app.core.config import settings

_session = aioboto3.Session()


def _client_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {"region_name": settings.SQS.REGION}
    if settings.SQS.ENDPOINT_URL is not None:
        kwargs["endpoint_url"] = settings.SQS.ENDPOINT_URL
    if settings.SQS.ACCESS_KEY_ID is not None:
        kwargs["aws_access_key_id"] = settings.SQS.ACCESS_KEY_ID
    if settings.SQS.SECRET_ACCESS_KEY is not None:
        kwargs["aws_secret_access_key"] = settings.SQS.SECRET_ACCESS_KEY
    return kwargs


@asynccontextmanager
async def sqs_client() -> AsyncIterator[Any]:
    async with _session.client("sqs", **_client_kwargs()) as client:
        yield client


def build_queue_url(queue_name: str, account_id: str) -> str:
    host = settings.SQS.ENDPOINT_URL or f"https://sqs.{settings.SQS.REGION}.amazonaws.com"
    return f"{host}/{account_id}/{queue_name}"
