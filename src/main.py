import logfire
from fastapi import FastAPI

from app.api.v1 import endpoints  # noqa: F401
from app.api.v1.router import router as v1_router
from app.core.config import settings

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

app = FastAPI(title="SaaS Catalog Analyzer")
logfire.instrument_fastapi(app)
app.include_router(v1_router)
