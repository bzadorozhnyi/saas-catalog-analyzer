import logfire
from fastapi import FastAPI

from app.api.v1 import endpoints  # noqa: F401
from app.api.v1.router import router as v1_router
from app.core.observability import configure_logfire

configure_logfire()

app = FastAPI(title="SaaS Catalog Analyzer")
logfire.instrument_fastapi(app)
app.include_router(v1_router)
