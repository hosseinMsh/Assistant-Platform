"""Tests for confirmation state machine and double-execution prevention."""
import json
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.anyio
async def test_atomic_claim_success():
    stored = json.dumps({
        "session_id": "sess-1",
        "tool": "notify.send_one",
        "arguments": {},
        "execution_id": "exec-1",
        "conversation_id": "conv-1",
        "claimed": False,
    })
    mock_redis = AsyncMock()
    mock_redis.eval = AsyncMock(return_value=stored)

    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import atomic_claim_confirmation
        result = await atomic_claim_confirmation("confirm-id-1")

    assert result is not None
    assert result["session_id"] == "sess-1"
    assert result["tool"] == "notify.send_one"


@pytest.mark.anyio
async def test_atomic_claim_already_claimed():
    """Second claim must return None — prevents double execution."""
    mock_redis = AsyncMock()
    mock_redis.eval = AsyncMock(return_value=None)  # already claimed

    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import atomic_claim_confirmation
        result = await atomic_claim_confirmation("confirm-id-1")

    assert result is None


@pytest.mark.anyio
async def test_atomic_claim_expired():
    """Expired confirmation (Redis returns None) → returns None."""
    mock_redis = AsyncMock()
    mock_redis.eval = AsyncMock(return_value=None)

    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import atomic_claim_confirmation
        result = await atomic_claim_confirmation("expired-id")

    assert result is None


@pytest.mark.anyio
async def test_create_confirmation_stores_execution_id():
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()

    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import create_confirmation
        confirm_id = await create_confirmation(
            session_id="sess-1",
            tool="notify.send_one",
            arguments={"message": "test"},
            execution_id="exec-42",
            conversation_id="conv-42",
        )

    assert confirm_id
    call_args = mock_redis.setex.call_args
    stored = json.loads(call_args[0][2])
    assert stored["execution_id"] == "exec-42"
    assert stored["conversation_id"] == "conv-42"
    assert stored["claimed"] is False


@pytest.mark.anyio
async def test_cancel_confirmation():
    stored = json.dumps({
        "session_id": "sess-1",
        "tool": "notify.send_one",
        "arguments": {},
        "execution_id": "exec-1",
        "conversation_id": "conv-1",
        "claimed": False,
    })
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=stored)
    mock_redis.delete = AsyncMock()

    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import get_confirmation, delete_confirmation
        pending = await get_confirmation("confirm-1")
        assert pending is not None
        assert pending["session_id"] == "sess-1"
        await delete_confirmation("confirm-1")
        mock_redis.delete.assert_called_once()


@pytest.mark.anyio
async def test_confirmation_wrong_session():
    """Confirmation belonging to a different session must be rejected."""
    stored = json.dumps({
        "session_id": "owner-session",
        "tool": "notify.send_one",
        "arguments": {},
        "execution_id": "exec-1",
        "conversation_id": "conv-1",
        "claimed": False,
    })
    mock_redis = AsyncMock()
    mock_redis.eval = AsyncMock(return_value=stored)

    with patch("app.auth.session.get_redis", return_value=mock_redis):
        from app.auth.session import atomic_claim_confirmation
        result = await atomic_claim_confirmation("confirm-id")

    assert result is not None
    assert result["session_id"] == "owner-session"
    # The service layer checks session_id — tested in test_backend.py
