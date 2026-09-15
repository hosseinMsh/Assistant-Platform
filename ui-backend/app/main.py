from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import new_request_id, setup_logging
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    yield


app = FastAPI(title="UI Backend", version="2.1.0", docs_url="/docs", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = new_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(ws_router)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.1.0"}
