from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.exception_handlers import exception_handler
from app.core.llm_call_batcher import llm_call_batcher
from app.core.observability import configure_logfire
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from router import router as api_router

configure_logfire()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await llm_call_batcher.start()
    try:
        yield
    finally:
        await llm_call_batcher.stop()


app = FastAPI(title="SaaS Catalog Analyzer", lifespan=lifespan)
logfire.instrument_fastapi(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(Exception, exception_handler)
app.include_router(api_router)
