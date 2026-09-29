from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3
from botocore.config import Config

from app.core.config import settings

_session = aioboto3.Session()


def _client_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {"region_name": settings.S3.REGION}
    if settings.S3.ENDPOINT_URL is not None:
        kwargs["endpoint_url"] = settings.S3.ENDPOINT_URL
        # LocalStack's S3 emulator only accepts path-style requests
        # (http://localhost:4566/<bucket>/<key>), not virtual-hosted-style.
        kwargs["config"] = Config(s3={"addressing_style": "path"})
    if settings.S3.ACCESS_KEY_ID is not None:
        kwargs["aws_access_key_id"] = settings.S3.ACCESS_KEY_ID
    if settings.S3.SECRET_ACCESS_KEY is not None:
        kwargs["aws_secret_access_key"] = settings.S3.SECRET_ACCESS_KEY
    return kwargs


@asynccontextmanager
async def s3_client() -> AsyncIterator[Any]:
    async with _session.client("s3", **_client_kwargs()) as client:
        yield client
