from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI

from app.core.exception_handlers import exception_handler
from app.core.llm_call_batcher import llm_call_batcher
from app.core.observability import configure_logfire
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
app.add_exception_handler(Exception, exception_handler)
app.include_router(api_router)
