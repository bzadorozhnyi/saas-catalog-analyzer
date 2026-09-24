import logfire
from fastapi import FastAPI

from app.core.exception_handlers import exception_handler
from app.core.observability import configure_logfire
from router import router as api_router

configure_logfire()

app = FastAPI(title="SaaS Catalog Analyzer")
logfire.instrument_fastapi(app)
app.add_exception_handler(Exception, exception_handler)
app.include_router(api_router)
