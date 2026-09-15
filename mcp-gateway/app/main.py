from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.core.logging import setup_logging
from app.api.routes.health import router as health_router
from app.api.routes.tools import router as tools_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    yield


app = FastAPI(
    title="MCP Gateway",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(tools_router)
