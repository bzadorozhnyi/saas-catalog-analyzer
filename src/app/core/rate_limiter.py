from fastapi import Request, Response
from slowapi import Limiter
from slowapi import _rate_limit_exceeded_handler as _slowapi_rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS.url,
    default_limits=["60/minute"],
)


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, RateLimitExceeded)
    return _slowapi_rate_limit_exceeded_handler(request, exc)
