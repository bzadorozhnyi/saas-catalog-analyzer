from typing import Annotated

from aiobotocore.client import AioBaseClient
from fastapi import Depends, Request


def get_s3_client(request: Request) -> AioBaseClient:
    return request.app.state.s3_client


S3ClientDep = Annotated[AioBaseClient, Depends(get_s3_client)]
