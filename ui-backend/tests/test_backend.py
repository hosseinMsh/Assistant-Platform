"""Integration-style tests for UI Backend routes."""
from __future__ import annotations
import uuid, json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import require_session
from app.core.database import get_db

FAKE_SESSION_ID = "fake-session-id-abc123"
FAKE_TOKEN      = "fake-access-token"
FAKE_CONV_ID    = str(uuid.uuid4())
FAKE_EXEC_ID    = str(uuid.uuid4())
FAKE_CONFIRM_ID = str(uuid.uuid4())


def _make_client(with_session: bool = True) -> TestClient:
    c = TestClient(app, raise_server_exceptions=False)
    if with_session:
        c.cookies.set("session_id", FAKE_SESSION_ID)
    return c


def _override_session():
    async def _dep(): return FAKE_SESSION_ID
    app.dependency_overrides[require_session] = _dep

def _override_db():
    from tests.conftest import _fake_db
    async def _dep():
        yield _fake_db
    app.dependency_overrides[get_db] = _dep


# ── Auth ───────────────────────────────────────────────────────────────────────

def test_create_session_raw_token():
    with patch("app.api.routes.auth.create_session", new_callable=AsyncMock, return_value=FAKE_SESSION_ID):
        r = _make_client(False).post("/api/v1/auth/session", json={"access_token": "validtoken123"})
    assert r.status_code == 200
    assert r.json()["authenticated"] is True

def test_create_session_bearer_token():
    with patch("app.api.routes.auth.create_session", new_callable=AsyncMock, return_value=FAKE_SESSION_ID) as mock_create:
        _make_client(False).post("/api/v1/auth/session", json={"access_token": "Bearer validtoken123"})
    called_with = mock_create.call_args[0][0]
    assert not called_with.lower().startswith("bearer")

def test_create_session_short_token():
    r = _make_client(False).post("/api/v1/auth/session", json={"access_token": "short"})
    assert r.status_code == 400

def test_create_session_empty_token():
    r = _make_client(False).post("/api/v1/auth/session", json={"access_token": ""})
    assert r.status_code == 400

def test_logout():
    with patch("app.api.routes.auth.delete_session", new_callable=AsyncMock):
        r = _make_client().post("/api/v1/auth/logout")
    assert r.status_code == 200

# ── Chat ───────────────────────────────────────────────────────────────────────

def test_chat_no_session():
    r = _make_client(False).post("/api/v1/chat", json={"message": "hello"})
    assert r.status_code == 401

def test_chat_plain_message():
    from app.schemas.chat import MessageResponse
    mock_result = MessageResponse(conversation_id=uuid.UUID(FAKE_CONV_ID), message="سلام!")
    _override_session(); _override_db()
    with patch("app.api.routes.chat.get_token", new_callable=AsyncMock, return_value=FAKE_TOKEN), \
         patch("app.api.routes.chat.handle_chat", new_callable=AsyncMock, return_value=mock_result):
        r = _make_client().post("/api/v1/chat", json={"message": "سلام"})
    assert r.status_code == 200
    assert r.json()["type"] == "message"

def test_chat_confirmation_required():
    from app.schemas.chat import ConfirmationRequiredResponse, NotificationPreview
    mock_result = ConfirmationRequiredResponse(
        conversation_id=uuid.UUID(FAKE_CONV_ID),
        confirmation_id=FAKE_CONFIRM_ID,
        execution_id=FAKE_EXEC_ID,
        tool="notify.send_one",
        preview=NotificationPreview(userName="1234567890", providerType=1, channel="SMS", message="test"),
    )
    _override_session(); _override_db()
    with patch("app.api.routes.chat.get_token", new_callable=AsyncMock, return_value=FAKE_TOKEN), \
         patch("app.api.routes.chat.handle_chat", new_callable=AsyncMock, return_value=mock_result):
        r = _make_client().post("/api/v1/chat", json={"message": "ارسال اعلان"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "confirmation_required"
    assert data["execution_id"] == FAKE_EXEC_ID

def test_confirm_once_succeeds():
    from app.schemas.chat import ToolResultResponse
    _override_session(); _override_db()
    with patch("app.api.routes.chat.get_token", new_callable=AsyncMock, return_value=FAKE_TOKEN), \
         patch("app.api.routes.chat.handle_confirm", new_callable=AsyncMock,
               return_value=ToolResultResponse(success=True, message="ok")):
        r = _make_client().post("/api/v1/chat/confirm", json={"confirmation_id": FAKE_CONFIRM_ID})
    assert r.status_code == 200
    assert r.json()["success"] is True

def test_confirm_twice_second_fails():
    from app.chat.service import ConfirmationError
    _override_session(); _override_db()
    with patch("app.api.routes.chat.get_token", new_callable=AsyncMock, return_value=FAKE_TOKEN), \
         patch("app.api.routes.chat.handle_confirm", new_callable=AsyncMock,
               side_effect=ConfirmationError("already used")):
        r = _make_client().post("/api/v1/chat/confirm", json={"confirmation_id": FAKE_CONFIRM_ID})
    assert r.status_code == 404

def test_confirm_wrong_owner():
    from app.chat.service import ConfirmationError
    _override_session(); _override_db()
    with patch("app.api.routes.chat.get_token", new_callable=AsyncMock, return_value=FAKE_TOKEN), \
         patch("app.api.routes.chat.handle_confirm", new_callable=AsyncMock,
               side_effect=ConfirmationError("wrong session")):
        r = _make_client().post("/api/v1/chat/confirm", json={"confirmation_id": "stolen"})
    assert r.status_code == 404

def test_cancel_action():
    _override_session(); _override_db()
    with patch("app.api.routes.chat.handle_cancel", new_callable=AsyncMock):
        r = _make_client().post("/api/v1/chat/cancel", json={"confirmation_id": FAKE_CONFIRM_ID})
    assert r.status_code == 200
    assert r.json()["cancelled"] is True

# ── Session unit ───────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_session_stores_token():
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()
    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import create_session
        session_id = await create_session("my-real-token")
    assert len(session_id) > 20
    stored = json.loads(mock_redis.setex.call_args[0][2])
    assert stored["token"] == "my-real-token"
    assert stored["token_hash"] != "my-real-token"

@pytest.mark.anyio
async def test_get_token_from_session():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=json.dumps({"token": "my-token", "token_hash": "abc"}))
    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import get_token
        assert await get_token("some-session") == "my-token"

@pytest.mark.anyio
async def test_invalid_session_returns_none():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import get_session
        assert await get_session("nonexistent") is None
