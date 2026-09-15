"""Pytest configuration — mock external services before app import."""
from unittest.mock import MagicMock, AsyncMock, patch
import sqlalchemy.ext.asyncio as _sa_async

# 1. Mock SQLAlchemy engine at import time (before app imports it)
_sa_async.create_async_engine = lambda *a, **kw: MagicMock()

# 2. Mock Redis globally so no real connection is attempted
import redis.asyncio as _redis_mod
_mock_redis = AsyncMock()
_mock_redis.get = AsyncMock(return_value=None)
_mock_redis.setex = AsyncMock(return_value=True)
_mock_redis.delete = AsyncMock(return_value=1)
_mock_redis.eval = AsyncMock(return_value=None)
_redis_mod.from_url = MagicMock(return_value=_mock_redis)

# 3. Override get_db to yield a mock session
from app.core import database as _db_module
_fake_db = AsyncMock()
_fake_db.execute = AsyncMock()
_fake_db.flush = AsyncMock()
_fake_db.commit = AsyncMock()
_fake_db.rollback = AsyncMock()
_fake_db.add = MagicMock()

async def _fake_get_db():
    yield _fake_db

_db_module.get_db = _fake_get_db

# Also patch AsyncSessionLocal used in ws.py
_db_module.AsyncSessionLocal = MagicMock()

# 4. Override FastAPI dependencies so session checks pass in tests
from app.main import app
from app.core.dependencies import require_session as _require_session
from app.core.database import get_db as _get_db

# These will be overridden per-test as needed, but provide defaults
import pytest

@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """Reset dependency overrides after each test."""
    original = dict(app.dependency_overrides)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)
